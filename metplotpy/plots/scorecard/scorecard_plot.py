"""
Command-line (no database) scorecard.

One YAML file drives the whole pipeline:

    1. reformat   MET .stat files into per-line-type tables        (METdataio)
    2. subset     rows using subset_params in the YAML
    3. per-case   statistics (SumStat) or aggregation (AggStat)    (METcalcpy)
    4. p-values   scorecard_stats.txt, one DIFF_SIG value per cell (METcalcpy)
    5. render     the scorecard with scorecard_render.py           (matplotlib)

Usage (from the METplotpy repo root):
    python -m metplotpy.plots.scorecard.scorecard_plot <config.yaml>

Look and feel (title, palette, labels, formats...) are set in the optional
`scorecard_style` block of the YAML; see scorecard_render.render_from_config.
"""
import os, sys
import fnmatch
import itertools
import requests
import json
import re
import pandas as pd
from datetime import datetime
from metplotpy.plots import util as plot_util
from METreformat import write_stat_ascii
from METdbLoad.ush.read_data_files import ReadDataFiles
from METdbLoad.ush.read_load_xml import XmlLoadFile
from METreformat.write_stat_ascii import WriteStatAscii
from metcalcpy.util.safe_log import safe_log
from metcalcpy import logging_config
from metcalcpy import scorecard
from metcalcpy.agg_stat import AggStat
from metcalcpy.sum_stat import SumStat
try:
    from metplotpy.plots.scorecard.scorecard_render import render_from_config
except ImportError:  # e.g. run from inside the scorecard directory
    from scorecard_render import render_from_config


class ScorecardPlot():
    def __init__(self, configs):
        # Assign the instance attributes based on config file settings
        self.configs = configs

        #
        # Logging and output location contain information for
        # all steps
        #
        self.output_dir = configs['output_dir']
        os.makedirs(self.output_dir, exist_ok=True)
        self.log_dir = configs['log_dir']
        # self.event_equalize = configs['event_equalize']
        self.event_equalize = False
        os.makedirs(self.log_dir, exist_ok=True)
        self.log_filename = os.path.join(self.log_dir, configs['log_filename'])
        self.log_level = configs['log_level']
        self.logger = logging_config.setup_logging(configs)

        logger = self.logger
        safe_log(logger, "debug", "Initializing ScorecardPlot with parameters")

        #
        # Input data
        #
        self.input_dir = configs['met_stat_input']
        self.ymd_start = configs['ymd_start']
        self.ymd_end = configs['ymd_end']

        # increment datetime in days
        self.increment = configs['increment']
        self.init = configs['init']

        # Optional glob pattern(s) selecting which .stat files to read from each
        # date directory, e.g. '*grid2obs*.stat'.  Default: every .stat file.
        patterns = configs.get('stat_file_pattern', ['*.stat'])
        if isinstance(patterns, str):
            patterns = [patterns]
        self.stat_file_patterns = patterns

        # What to do when a date directory (or the files in it) is missing:
        #   'skip'  - drop that date for ALL models (keeps the model comparison
        #             paired), carry on, and report what was skipped
        #   'error' - stop at the first missing directory or file
        self.on_missing_input = str(configs.get('on_missing_input', 'skip')).lower()
        if self.on_missing_input not in ('skip', 'error'):
            raise ValueError("on_missing_input must be 'skip' or 'error', "
                             f"got {configs.get('on_missing_input')!r}")
        self.missing_input = []     # (date, model/variable label, reason)
        self.dates_total = None
        self.dates_used = None

        # Stop with an error if a statistic listed in stats_list never makes it
        # into scorecard_stats.txt (otherwise it silently disappears).
        self.fail_on_missing_stats = bool(configs.get('fail_on_missing_stats', True))

        #
        # For reformatter
        #
        self.linetype = str(configs['linetype'])
        self.reformat_flag = configs['reformat_needed']
        self.reformat_params = {}
        self.reformat_params['input_stats_aggregated'] = configs['has_confidence_stats']
        self.reformat_params['log_directory'] = self.log_dir
        self.reformat_params['output_dir'] = self.output_dir
        reformat_output_fname_parts = ["reformatted_", self.linetype, ".txt"]
        reformat_output_fname = ''.join(reformat_output_fname_parts)
        self.reformat_params['output_filename'] = os.path.join(self.output_dir, reformat_output_fname)
        self.reformat_params['input_data_dir'] = configs['met_stat_input']
        self.reformat_params['log_directory'] = self.log_dir
        self.reformat_params['log_filename'] = self.log_filename
        self.reformat_params['log_level'] = self.log_level
        self.reformat_params['line_type'] = self.linetype

        #
        # For subsetting
        #
        self.subset_params: dict = configs['subset_params']

        subsetted_fname = "filtered.txt"
        self.subsetted_filename = os.path.join(self.output_dir, subsetted_fname)
        if 'fcst_var' not in self.subset_params.keys():
            msg = "Missing fcst var in config file.  This is needed to subset the input data."
            safe_log(logger, "error", msg)


        #
        # For p-values via METcalcpy scorecard module
        #
        self.append_sc_runs: bool = configs['append_subsequent']

        self.derived_series_1: list[list] = self.create_derived_series()
        agg_fname = self.linetype.upper() + "_aggregated.data"
        self.aggstat_filename = os.path.join(self.output_dir, agg_fname)

        sc_stat_fname = "scorecard_stats.txt"
        self.scorecard_stats_output_filename = os.path.join(self.output_dir, sc_stat_fname)

        self.scorecard_stats_indy_var = self.subset_params['indep_variable']
        self.scorecard_stats_indy_vals = self.subset_params['indep_values']

        # remove the fcs_init_beg key from the subset parameters if it
        # is present. The scorecard doesn't use it and it results in the inability
        # to correctly create cartesian products.
        if 'fcst_init_beg' in self.subset_params.keys():
            self.subset_params.pop('fcst_init_beg')

        self.scorecard_stats_series_val = self.subset_params
        self.scorecard_stats_statslist = self.subset_params['stats_list']

        # num of days, used in bootstrapping
        self.sample_size = int(configs['sample_size'])
        self.pval_method: str = configs['pval_method']



    def find_input_files(self, final_list, all_values, var_index, all_dates) -> list:
        """
        Find the .stat files matching stat_file_pattern in every input directory.

        A date is only used if EVERY directory for that date (i.e. every model) has
        matching files.  Otherwise the date is dropped for all models, so the models
        are compared on the same sample, and what was skipped is recorded in
        self.missing_input (printed at the end by report_missing_input()).
        With on_missing_input: error the first missing directory/file stops the run.

        Args:
            final_list: input directories, one per combination of the ${...} variables
            all_values: the variable values behind each directory (same order)
            var_index:  position -> variable name for the values in all_values
            all_dates:  every date requested (strings in the 'init' format)

        Returns:
            list of file paths
        """
        date_pos = [i for i, n in var_index.items() if n == 'init']
        # variables that differ between directories (besides the date), e.g. model
        label_pos = [i for i, n in var_index.items()
                     if n != 'init' and len({v[i] for v in all_values}) > 1]

        files_by_dir, problem_by_dir, info_by_dir = {}, {}, {}
        for curr_dir, curr_value in zip(final_list, all_values):
            date = curr_value[date_pos[0]] if date_pos else None
            label = ", ".join(f"{var_index[i]}={curr_value[i]}" for i in label_pos)
            info_by_dir[curr_dir] = (date, label)
            if not os.path.isdir(curr_dir):
                problem_by_dir[curr_dir] = "directory not found"
                continue
            stat_files = sorted(f for f in os.listdir(curr_dir) if f.endswith(".stat"))
            matched = [f for f in stat_files
                       if any(fnmatch.fnmatch(f, p) for p in self.stat_file_patterns)]
            if matched:
                files_by_dir[curr_dir] = [os.path.join(curr_dir, f) for f in matched]
            else:
                problem_by_dir[curr_dir] = (f"no files matching {self.stat_file_patterns} "
                                            f"(found: {stat_files if stat_files else 'no .stat files'})")

        if problem_by_dir and (self.on_missing_input == 'error' or not date_pos):
            bad_dir = next(iter(problem_by_dir))
            raise FileNotFoundError(f"{bad_dir}: {problem_by_dir[bad_dir]}")

        # A date is complete only if every one of its directories has files
        bad_dates = {}
        for curr_dir, reason in problem_by_dir.items():
            date, label = info_by_dir[curr_dir]
            bad_dates.setdefault(date, []).append((label, reason))
        used_dates = [d for d in all_dates if d not in bad_dates]
        for date in all_dates:
            for label, reason in bad_dates.get(date, []):
                self.missing_input.append((date, label, reason))
                safe_log(self.logger, 'warning',
                         f"Skipping {date} for all models: {label}: {reason}")
        self.dates_total, self.dates_used = len(all_dates), len(used_dates)
        if not used_dates:
            raise FileNotFoundError(
                f"No date has matching files for every model ({len(all_dates)} dates "
                f"checked, patterns {self.stat_file_patterns}); first problem: "
                f"{self.missing_input[0]}")

        all_files = []
        for curr_dir in final_list:
            if info_by_dir[curr_dir][0] in used_dates:
                all_files.extend(files_by_dir[curr_dir])
        safe_log(self.logger, 'info',
                 f"Reading {len(all_files)} .stat file(s) matching "
                 f"{self.stat_file_patterns} for {len(used_dates)} of {len(all_dates)} date(s)")
        return all_files

    def report_missing_input(self) -> None:
        """Print (and log) which dates were skipped because input was missing."""
        if not self.missing_input:
            return
        lines = [f"WARNING: {len(self.missing_input)} input problem(s); "
                 f"used {self.dates_used} of {self.dates_total} date(s).",
                 "Skipped for ALL models so the comparison stays paired:"]
        for date, label, reason in self.missing_input:
            lines.append(f"  {date}  {label}: {reason}")
        msg = "\n".join(lines)
        print("\n" + msg)
        safe_log(self.logger, 'warning', msg)

    def read_input(self) -> pd.DataFrame:

        """
          Retrieve all the input data from directories specified in the YAML config
          file from the input_dir, start date, end date, and increment.

          Args:

          Returns:

         a pandas dataframe containing the data

        """
        # Get all the dates of interest
        increment = int(self.increment)
        date_start = datetime.strptime(self.ymd_start, self.init)
        date_end = datetime.strptime(self.ymd_end, self.init)

        all_dates = []
        while date_start <= date_end:
            all_dates.append(date_start.strftime(self.init))
            date_start = date_start + pd.Timedelta(days=increment)

        # Substitute variables that aren't "init"

        # keep track of the index of variable names, to be used later when creating
        # relevant file directories
        matches = re.finditer(r'\$\{([^}^{]+)\}', self.input_dir)
        yaml_var_vals = {}
        var_index = {}

        for idx, curr_match in enumerate(matches):
            curr_matchobj = curr_match[0]
            var = re.match(r'.*{(.*)\}', curr_matchobj)
            # user's "variable" name in the input_dir setting
            match = var.group(1)

            # evaluate the non-init variables from  'init'
            if match != 'init':
                if isinstance(self.configs[match], list):
                    # variable's value is a list of settings
                    var_index[idx] = match
                    yaml_var_vals[match] = self.configs[match]
                else:
                    # variable's value is a single value
                    var_index[idx] = match
                    yaml_var_vals[match] = [self.configs[match]]
            else:
                # init variable, defines date directories
                var_index[idx] = match
                yaml_var_vals[match] = all_dates

        all_var_vals = yaml_var_vals.values()
        all_values = []

        # Get cartesian product of the variable values (pass in the unpacked all_var_vals
        # to get the desired cartesian product)
        for _ in itertools.product(*all_var_vals):
            all_values.append(_)

        # Create the full input directories with all variables substituted with actual values
        final_list = []

        for curr_value in all_values:
            string = self.input_dir
            for v_idx in var_index:
                pattern = var_index[v_idx]
                repl = curr_value[v_idx]
                if v_idx > 0:
                    string = result
                result = re.sub(pattern, repl, string)

                # Remove the $, {, and } from each directory path
                result = re.sub('\\$', '', result)
                result = re.sub('{', '', result)
                result = re.sub('}', '', result)

            final_list.append(result)

        all_files = self.find_input_files(final_list, all_values, var_index, all_dates)

        # Read in the files into a dataframe using METdataio's METdbLoad modules

        # Replacing the need for an XML specification file, pass in the XMLLoadFile and
        # ReadDataFile parameters
        rdf_obj: ReadDataFiles = ReadDataFiles(self.logger)
        xml_loadfile_obj: XmlLoadFile = XmlLoadFile(None)
        flags = xml_loadfile_obj.flags
        line_types = xml_loadfile_obj.line_types
        flags["load_stat"] = True
        rdf_obj.read_data(flags, all_files, line_types)
        return rdf_obj.stat_data


    def create_derived_series(self) -> list[list]:
        """
           Create all the derived series settings based on the fcst level, model names,
           fcst hour, fcst variable, statistics

           Args:
              configs (dict):

          Returns:
              A list of lists representing the derived series required by METcalcpy's
              scorecard.py module

        """
        fcst_leads = self.subset_params['fcst_lead']
        models = self.subset_params['model']
        stats = self.subset_params['stats_list']
        fcst_levs = self.subset_params['fcst_lev']
        fcst_var = self.subset_params['fcst_var']

        # Any additional fixed filter dimensions in subset_params (e.g. obtype)
        # have to be embedded into the derived-series comparison string too, or
        # METcalcpy's _get_derived_points() will intersect them away to an empty
        # list and silently produce zero derived points. Inserted between
        # fcst_var and stats so model stays at index 1 (used below) and stat
        # stays last (used by METcalcpy as the stat name).
        # If we know all the additional dims, should we just add to known_keyS?
        known_keys = {'fcst_lead', 'model', 'stats_list', 'fcst_lev', 'fcst_var',
                      'indep_variable', 'indep_values'}
        extra_dims = [v for k, v in self.subset_params.items()
                      if k not in known_keys and isinstance(v, list)]

        # Create the Cartesian product of the above
        result = list(itertools.product(fcst_levs, models, fcst_leads, fcst_var, *extra_dims, stats))

        # Make all elements strings, to enable joining the fcst lead, model name, etc
        # based on model name into the format (level model fcst_hr variable stat:
        #          Z2 ModelA 60000 TMP RMSE
        modelA = []
        modelB = []

        for _ in result:
            if _[1] == models[0]:
                modelA_strs = [(str(i)) for i in _]
                modelA.append(modelA_strs)

            else:
                modelB_strs = [(str(i)) for i in _]
                modelB.append(modelB_strs)

        # If models don't have the same number of data points, exit with a message.
        if len(modelA) != len(modelB):
            msg = (f"Different number of {models[0]} and {models[1]} data.  Please check your"
                   f"data.  ")
            sys.exit(msg)

        # Join the components into one string
        modelA_strs = [" ".join(i) for i in modelA]
        modelB_strs = [" ".join(i) for i in modelB]

        # Group the modelA and modelB strings with the same fcst level, fcst hr,
        # fcst var, and stat values
        modelA_B = [list(i) for i in zip(modelA_strs, modelB_strs)]

        # Add the 'DIFF_SIG' directive to each item
        [i.append("DIFF_SIG") for i in modelA_B]

        return modelA_B


    def __repr__(self):

        class_name = type(self).__name__
        return (f"{class_name}(config={self.configs!r},)")


    def __str__(self):
        return f'(config={self.configs!r})'


    def check_for_invalid_columns(self, df: pd.DataFrame) -> None:
        """
               Verify that columns requested in YAML config file
               are valid columns.  Exit if a requested column does not
               exist in the data.  Non-existent columns are logged.

          Args:
              df (pd.DataFrame):  The dataframe containing MET data

          Returns:
               None: exits if there are any columns requested that don't exist in the
                        data.

        """

        safe_log(self.logger, 'debug', 'Check for requested columns in data.')

        # Retrieve all the column names in the data frame:
        all_cols = df.columns.to_list()

        exclude_key = ['Idx', 'indep_values', 'indep_variable', 'stats_list', ]
        filter_keys = [cols for cols in self.subset_params.keys() if cols not in exclude_key]

        invalid_cols = []
        # add the independent variable to the keys to check
        indep_var = self.subset_params['indep_variable']
        filter_keys.append(indep_var)

        # Check the columns
        for cur_fkey in filter_keys:
            # don't include the stats and indep values in the check
            if cur_fkey not in all_cols:
                invalid_cols.append(cur_fkey)
                msg = f" Cannot filter on non-existent column. {cur_fkey!r} is not a valid column name. "
                safe_log(self.logger, 'error', msg)

        if len(invalid_cols) > 0:
            safe_log(self.logger, 'error', 'Exiting.  Check your data for the columns requested.')
            sys.exit("Error:" + msg)


    def subset_data(self, subset_df:pd.DataFrame) -> pd.DataFrame:
        """
            Invoke this prior to invoking METcalcpy agg_stat.
            Subset data based on independent variable and its
            corresponding values, and any other columns in the data.
            This step eliminates the need for a database.

            Args:

                subset_df (pd.DataFrame): The  dataframe containing the MET stat data with
                                        all columns labelled

           Returns:
               result (pd.DataFrame): a dataframe after filtering/subsetting data based on criteria in the YAML config file
               Also saves a file that contains only the relevant information as specified in
               the YAML config file and also

        """
        safe_log(self.logger, 'debug', 'Filter data based on subset_params in the config file.')
        working_df = subset_df.copy()

        # Exit if there are any requested columns that don't exist in the data
        self.check_for_invalid_columns(working_df)

        # Replace the 'indep_variable' key with its value,
        # replace the 'indep_values' key with its values, and
        # replace stats_list keyname with stat_name
        filter_keys = self.subset_params
        indep_variable = filter_keys['indep_variable']
        indep_var_vals = filter_keys['indep_values']
        filter_keys[indep_variable] = indep_var_vals
        if self.configs['has_confidence_stats']  == False:
            # update the stats names in stats list with the linetype prefixed to the
            # stat name
            linetyped_stats = []
            for curr in filter_keys['stats_list']:
                lt_stat_name = "".join(self.linetype + "_" + curr)
                linetyped_stats.append(lt_stat_name)
            filter_keys['stat_name'] = linetyped_stats
        else:
            filter_keys['stat_name'] = filter_keys['stats_list']
        del filter_keys['indep_variable']
        del filter_keys['indep_values']
        del filter_keys['stats_list']

        # Create queries for column names specified in the subset_params settings.
        # 'OR' all the values corresponding to each key, and 'AND' all of the
        # key "segments" to create a final query.

        # Keep the query tokens ordered by column names
        all_queries_by_cols = {}

        # Generate all the query tokens for each
        # column name.  A query token is a combination of
        # the column with each value with form
        # df[column_name] == val
        for idx, column_name in enumerate(filter_keys):
            queries_by_column = []

            # Get the values for the current filter key
            values = self.subset_params[column_name]
            idx_last_value = len(values) - 1

            for idx_val, cur_value in enumerate(values):
                cur_value = cur_value.strip()
                if column_name == 'fcst_lead':
                    query_token = f' ({column_name} == {cur_value} )'
                else:
                    query_token = f' ({column_name} == "{cur_value}" )'

                # Add the 'OR' logic operator
                # between each value corresponding to this column
                if len(values) > 1 and idx_val != idx_last_value:
                    query_token = query_token + ' | '
                queries_by_column.append(query_token)
            all_queries_for_this_column = ''.join(queries_by_column)
            all_queries_by_cols[column_name] = all_queries_for_this_column

        # Add the appropriate parens and the 'AND'
        # logical operator between the query tokens based on column
        all_columns = all_queries_by_cols.keys()
        last_column = len(all_columns) - 1
        for idx, cur_col in enumerate(all_columns):
            values_for_col = all_queries_by_cols[cur_col]

            if idx != last_column:
                values_for_col_updated = "(" + values_for_col + " ) & "
            else:
                values_for_col_updated = "(" + values_for_col + " ) "

            # Add this to the "all queries" dictionary to keep the value query
            # tokens grouped by the column name (key)
            all_queries_by_cols[cur_col] = values_for_col_updated

        # Create the finished query string
        full_query_str_list = []
        for v in all_queries_by_cols.values():
            # only collect the values into a list to be joined later to create the full query
            full_query_str_list.append(v)

        full_query = "".join(full_query_str_list)

        result: pd.DataFrame = working_df.query(full_query)

        result.to_csv(self.subsetted_filename, header=True, index_label=False, index=False, sep='\t')

        return result


    def reformat_met_stat(self) -> pd.DataFrame:
        """
             Invoke the METdataio METreformatter's write_stat_ascii module to
             label all the headers in the MET .stat file based on linetype (specified in
             the YAML config file).

             Args:

             Returns:

                 reformatted_df (pd.DataFrame): The pandas dataframe containing the
                           reformatted data.


        """

        if self.reformat_flag:
            r_df = self.read_input()
            if r_df.size == 0:
                safe_log(self.logger, 'ERROR', "ERROR:  Input dataframe is empty.  Exiting")
                sys.exit()
            if os.path.exists(self.reformat_params['output_filename']):
                safe_log(self.logger, self.log_level, "Output file already exists, removing this file.")
                os.remove(self.reformat_params['output_filename'])

            stat_lines_obj: WriteStatAscii = WriteStatAscii(self.reformat_params, self.logger)
            reformatted_df = stat_lines_obj.write_stat_ascii(r_df, self.reformat_params)
            return reformatted_df
        else:
            safe_log(self.logger, self.log_level, "Reformatting not requested")



    def set_dtypes(self, reformatted_df:pd.DataFrame) -> pd.DataFrame:
        """
             Explicitly set the dtypes for all the columns in the reformatted dataframe
             to avoid dtype errors and avoid relying on the soon-to-be deprecated
             low_memory=False when reading data.

             Use the MET met_column_types.json file to retrieve the appropriate
             dtypes.

             Args:
                reformatted_df (pd.DataFrame): The pandas dataframe containing  data with reformatted MET
                                                            data (i.e. all stat columns are split between
                                                            the stat_name and stat_val columns, and
                                                            all other unlabelled columns are
                                                            appropriately labelled).

             Returns:
                 dtype_df (pd.DataFrame): A dataframe that has had all the column
                 dtypes explicitly set.

        """

        # Retrieve the met_column_types.json file from the MET repository's
        # develop branch
        url = "https://raw.githubusercontent.com/dtcenter/MET/refs/heads/develop/data/table_files/met_column_types.json"
        response = requests.get(url)
        dtypes_file = os.path.join(os.getcwd(), "dtypes.txt")
        with open(dtypes_file, "w") as f:
            f.write(response.text)

        with open(dtypes_file) as dtf:
           met_types:dict = json.load(dtf)

        linetype = self.linetype.upper()
        dtype_df = reformatted_df.copy(deep=True)
        all_df_dtypes = dtype_df.dtypes

        # The dtype index corresponds to the name of the column
        idx = all_df_dtypes.index

        # Columns that are added and not part of the original MET input
        ignore_cols = ['fcst_init_beg', 'stat_name', 'stat_value']

        # Assign the dtypes from the MET json file to the corresponding column in
        # the dataframe (of the reformatted data).
        accepted = ["str", "int64", "float64"]
        for i in idx:
            # column names in json file are upper case, need to convert the dataframe's
            # columns to upper case
            met_col = str(i).upper()

            if i not in ignore_cols:
                if dtype_df[i].dtype not in accepted:
                    print(f"WARNING {i}: {dtype_df[i].dtype}, converting to {dtype_df[i].astype("str")}")

                dtype_df.astype({i:met_types[linetype][met_col]}).dtypes

        return dtype_df

    def calculate_agg_stats(self, subset_df:pd.DataFrame):
        """
            Calculate the CI's using METcalcpy agg_stat.py

            Args:
                subset_df (pd.DataFrame): The dataframe containing subsetted data.

            Returns:
                aggregated_df (pd.DataFrame): Dataframe with the CI's calculated

        """
        # fname = "reformatted_" + self.configs['linetype'] + ".txt"
        fname = "filtered.txt"
        input_file = os.path.join(self.configs['output_dir'], fname)
        agg_stat_configs = {}

        # Generate the configuration settings needed by METcalcpy's agg_stat
        # module from the scorecard yaml config file.
        # subset_df.to_csv(input_file)
        agg_stat_configs['agg_stat_input'] = input_file
        outname = self.configs['linetype'] + "_aggregated.data"
        agg_stat_configs['agg_stat_output'] = os.path.join(self.configs['output_dir'], outname )
        agg_stat_configs['alpha'] = 0.05
        agg_stat_configs['append_to_file'] = "null"
        agg_stat_configs['circular_block_bootstrap'] = True
        agg_stat_configs['derived_series_1'] = []
        agg_stat_configs['derived_series_2'] = []
        agg_stat_configs['event_equal']  = self.event_equalize

        # fcst_var_val_1 is the fcst_var and the stat (stat name is pre-fixed with
        # the linetype e.g. RMSE becomes ECNT_RMSE for linetype ECNT and
        # stat in the stat_list of the scorecard YAML).
        fcst_var = self.configs['subset_params']['fcst_var'][0]
        stats_list = self.configs['subset_params']['stat_name']
        agg_stat_configs['fcst_var_val_1']= {fcst_var:stats_list}
        agg_stat_configs['fcst_var_val_2'] = {}
        agg_stat_configs['indy_vals'] = self.configs['subset_params']['fcst_lead']
        agg_stat_configs['indy_var'] = 'fcst_lead'
        agg_stat_configs['line_type'] = str(self.configs['linetype']).lower()
        agg_stat_configs['list_stat_1'] = stats_list
        agg_stat_configs['list_stat_2'] = []
        agg_stat_configs['method'] = 'perc'
        agg_stat_configs['num_iterations'] = 1
        agg_stat_configs['num_threads'] = -1
        agg_stat_configs['random_seed'] =  None
        # agg_stat_configs['series_val_1'] = {'model':self.configs['subset_params']['model']}
        agg_stat_configs['series_val_1'] = self.configs['subset_params']
        agg_stat_configs['series_val_2'] = []

        msg = "Calculating CI for "+ self.configs['linetype'] +" with agg_stat"
        safe_log(self.logger, self.log_level, msg)
        AGG_STAT = AggStat(agg_stat_configs)
        AGG_STAT.calculate_stats_and_ci()
        self.agg_stat_outfile =  agg_stat_configs['agg_stat_output']
        safe_log(self.logger, self.log_level, "Finished calculating CI with agg_stat")

        return pd.read_csv(self.agg_stat_outfile, sep='\t', index_col=False)

    def calculate_sum_stats(self, subset_df: pd.DataFrame):
        """
            Calculate per-case/per-day statistics using METcalcpy's sum_stat.py,
            the same building block METviewer's own scorecard pipeline uses
            (see edu.ucar.metviewer.scorecard.rscript.SumPythonManager in
            METviewer, which runs sum_stat.py before scorecard.py -- agg_stat.py
            is a different METviewer feature, not part of the scorecard chain).

            Unlike calculate_agg_stats()/AggStat, this does NOT collapse multiple
            cases into one bootstrapped point estimate. It computes the requested
            statistic (e.g. MAE) independently for each row of the input data,
            preserving one row per case/valid-date -- which is what the scorecard's
            own DIFF_SIG significance calculation (_calculate_diff_sig_ncar/_emc)
            actually needs multiple values per (model, lead) group to compute.

            Args:
                subset_df (pd.DataFrame): The dataframe containing subsetted data,
                    as produced by process_X_for_agg() -- i.e. one row per case,
                    already filtered down to the requested stat (e.g. one row per
                    case tagged 'SAL1L2_MAE'), with stat_value left as NaN, to be
                    filled in here.

            Returns:
                summary_df (pd.DataFrame): Dataframe with stat_value populated,
                    one row per case, ready to feed into get_scorecard_stats().

        """
        fname = "filtered.txt"
        input_file = os.path.join(self.configs['output_dir'], fname)

        # sum_stat.py's calculate_statistic() dispatches to calculate_<stat_name>
        # using the *bare* stat name (e.g. 'mae', not 'sal1l2_mae') -- its own
        # line_type == 'sal1l2' special case renames columns to match SL1L2's
        # naming specifically so it can reuse the bare calculate_mae/etc.
        # functions. Our process_X_for_agg() output uses the LINETYPE_STATNAME
        # convention (matching AggStat's needs), so it has to be stripped back
        # to bare form here before sum_stat.py sees it.
        linetype_upper = str(self.configs['linetype']).upper()
        prefix = linetype_upper + '_'
        sum_stat_input_df = subset_df.copy()
        sum_stat_input_df['stat_name'] = sum_stat_input_df['stat_name'].apply(
            lambda s: s[len(prefix):] if isinstance(s, str) and s.startswith(prefix) else s)

        sum_stat_input_file = os.path.join(self.configs['output_dir'], "filtered_for_sum_stat.txt")
        sum_stat_input_df.to_csv(sum_stat_input_file, index=None, header=True, sep='\t', na_rep="NA")

        sum_stat_configs = {}

        # Generate the configuration settings needed by METcalcpy's sum_stat
        # module from the scorecard yaml config file. Deliberately NOT including
        # the bootstrap-specific keys AggStat needs (alpha, circular_block_bootstrap,
        # method, num_iterations, num_threads, random_seed) -- sum_stat.py doesn't
        # use them; it computes one value per row, no resampling.
        sum_stat_configs['sum_stat_input'] = sum_stat_input_file
        outname = self.configs['linetype'] + "_summary.data"
        sum_stat_configs['sum_stat_output'] = os.path.join(self.configs['output_dir'], outname)
        sum_stat_configs['event_equal'] = self.event_equalize
        sum_stat_configs['line_type'] = str(self.configs['linetype']).lower()

        fcst_var = self.configs['subset_params']['fcst_var'][0]
        stats_list = self.configs['subset_params']['stat_name']
        sum_stat_configs['fcst_var_val_1'] = {fcst_var: stats_list}
        sum_stat_configs['fcst_var_val_2'] = {}
        sum_stat_configs['indy_vals'] = self.configs['subset_params']['fcst_lead']
        sum_stat_configs['indy_var'] = 'fcst_lead'
        sum_stat_configs['list_stat_1'] = stats_list
        sum_stat_configs['list_stat_2'] = []
        sum_stat_configs['series_val_1'] = self.configs['subset_params']
        sum_stat_configs['series_val_2'] = {}
        sum_stat_configs['derived_series_1'] = []
        sum_stat_configs['derived_series_2'] = []
        sum_stat_configs['log_filename'] = self.configs.get('log_filename', '-')
        sum_stat_configs['log_level'] = self.configs.get('log_level', 'ERROR')

        msg = "Calculating per-case statistics for " + self.configs['linetype'] + " with sum_stat"
        safe_log(self.logger, self.log_level, msg)
        SUM_STAT = SumStat(sum_stat_configs)
        SUM_STAT.calculate_stats()
        self.sum_stat_outfile = sum_stat_configs['sum_stat_output']
        safe_log(self.logger, self.log_level, "Finished calculating per-case statistics with sum_stat")

        return pd.read_csv(self.sum_stat_outfile, sep='\t', index_col=False)



    def get_scorecard_stats(self, input_df:pd.DataFrame) -> pd.DataFrame:
        """
              Invoke the METcalcpy scorecard module to calculate the p-values.



              Args:
                  input_df (pd.DataFrame): The dataframe containing the reformated,
                  filtered, and aggregated (if applicable) data.
              Returns:
                 a dataframe that will be used to generate the
                 scorecard plot.

        """

        # Create the params expected by METcalcpy scorecard.py
        params = {}
        params['append_subsequent'] = self.append_sc_runs
        params['derived_series_1'] = self.derived_series_1
        params['ndays'] = self.sample_size
        params['pval_method'] = self.pval_method
        params['log_dir'] = self.log_dir
        params['log_filename'] = self.log_filename
        params['log_level'] = self.log_level
        params['scorecard_output'] = self.scorecard_stats_output_filename
        params['list_stat_1'] = self.scorecard_stats_statslist

        # ToDo put logic for whether agg stat was needed and use that output file
        # as input (CNT linetype does not require agg_stat.py, there are other linetypes
        # that also do not require agg_stat.py)
        if self.linetype == 'CNT':
            # use the reformatted output for scorecard stats input
            # remove the fcst_init_beg
            params['sum_stat_input'] = self.subsetted_filename
        else:
            print("METcalcpy agg_stat necessary")
            aggstat_filename = os.path.join(os.getcwd(), self.aggstat_filename)
            params['sum_stat_input'] = aggstat_filename

        params['sum_stat_output'] = self.scorecard_stats_output_filename
        params['series_val_1'] = self.scorecard_stats_series_val
        params['indy_var'] = self.scorecard_stats_indy_var
        params['indy_vals'] = self.scorecard_stats_indy_vals
        params['stats_list'] = self.scorecard_stats_statslist
        params['stat_flag'] = self.pval_method

        calcpy_sc = scorecard.Scorecard(params)
        # calcpy_sc.input_data= input_df
        calcpy_sc.calculate_scorecard_data()


    def check_requested_stats(self) -> None:
        """
        Make sure every statistic in stats_list actually reached scorecard_stats.txt.

        A statistic can be lost without any error (a name the reformatter never
        creates, a filter that matches nothing, ...), which leaves a scorecard that
        looks fine but is missing rows.  Raise an error, or only log one when
        fail_on_missing_stats is False.
        """
        stats_file = self.scorecard_stats_output_filename
        if not os.path.isfile(stats_file):
            raise FileNotFoundError(
                f"{stats_file} was not created; METcalcpy scorecard.py produced no output")
        stats_df = pd.read_csv(stats_file, sep="\t", dtype=str, keep_default_na=False)
        prefix = f"{self.linetype.upper()}_"
        found = {n.upper()[len(prefix):] if n.upper().startswith(prefix) else n.upper()
                 for n in stats_df['stat_name']}
        missing = [s for s in self.scorecard_stats_statslist if str(s).upper() not in found]
        if missing:
            msg = (f"Requested statistic(s) {missing} are not in {stats_file} "
                   f"(found: {sorted(found)}). They were filtered out or could not be "
                   f"computed upstream (reformat, subset or per-case step).")
            safe_log(self.logger, 'error', msg)
            if self.fail_on_missing_stats:
                raise RuntimeError(msg)

    def render_scorecard(self) -> list:
        """
        Draw the scorecard with scorecard_render.py (matplotlib only).  Reads the
        scorecard_stats.txt written by METcalcpy and derives the significance
        categories itself, for both the NCAR and EMC p-value methods.

        Look and feel come from the YAML: scorecard_title plus an optional
        scorecard_style block (title, subtitle, palette, show_values, markers,
        formats, dpi, label_map, model_names).  See scorecard_render.render_from_config.

        Returns:
            list of the files written (<output_dir>/scorecard.<format>)
        """
        models = self.subset_params.get('model', [])
        names = [models[0], models[1]] if len(models) >= 2 else None
        extra = None
        if self.dates_total and self.dates_used < self.dates_total:
            extra = f"{self.dates_used} of {self.dates_total} days"  # some dates skipped
        written = render_from_config(
            self.scorecard_stats_output_filename,
            os.path.join(self.output_dir, "scorecard"),
            style=self.configs.get('scorecard_style'),
            model_names=names,
            date_range=(self.ymd_start, self.ymd_end),
            title=self.configs.get('scorecard_title'),
            subtitle_extra=extra)
        safe_log(self.logger, 'info', f"Scorecard written: {', '.join(written)}")
        return written


# Should consider adding a step to remove all files associated with the run to make
# sure the current run isn't using old or stale files to generate the scorecard.


def main(config_filename=None):
    """
        Read in the YAML config file and perform steps needed
        to generate a scorecard plot.

    """
    # print(f"reading in the data: {datafile}")
    # df = pd.read_table(datafile)
    #
    # print(f"df: {df['stat_value']}")

    confs = plot_util.get_params(config_filename)
    sc = ScorecardPlot(confs)

    #
    #  Reformat the MET .stat file(s)
    #
    reformatted_df =  sc.reformat_met_stat()

    #
    # Explicitly set the dtype for each column using the MET json file
    #
    # dtype_df = sc.set_dtypes(reformatted_df)
    #
    #  Filter the data based on settings in the YAML config file
    #
    subset_df = sc.subset_data(reformatted_df)
    #
    # Calculate the aggregation statistics via METcalcpy agg_stat.py
    # module if needed
    if confs['has_confidence_stats']:
        print(f"Skip running agg_stat.py {sc.linetype} already has CI's calculated  ")
        aggregated_df = subset_df.copy()
        sc.aggstat_filename = sc.subsetted_filename
    else:
        print(f" Invoke  METcalcpy sum_stat.py to calculate per-case statistics for {sc.linetype} ")
        aggregated_df = sc.calculate_sum_stats(subset_df)
        sc.aggstat_filename = sc.sum_stat_outfile
    #
    # Get the p-values and scorecard categories
    #

    # input is dependent on whether agg_stat.py was used to calculate the CI's
    # CNT line type already has CI's
    _: pd.DataFrame = sc.get_scorecard_stats(aggregated_df)

    # Every requested statistic must be present, then draw the scorecard.
    sc.check_requested_stats()
    sc.render_scorecard()
    sc.report_missing_input()
    print("Finished")

if __name__ == "__main__":
    # print("Scorecard plotting")
    # datafile = "/Users/minnawin/Python_Scorecard_Dev/METcalcpy/metcalcpy/output/hrrr_rrfs_output.data"
    # main(datafile)
    main()
