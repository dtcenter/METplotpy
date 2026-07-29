import os, sys
import itertools
import re
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from metplotpy.external.plottable.plottable import Table
from metplotpy.external.plottable.plottable import ColumnDefinition
from metplotpy.external.plottable.plottable.plots import image
from metplotpy.plots import util as plot_util
import METdataio.METreformat.write_stat_ascii
from METdbLoad.ush.read_data_files import ReadDataFiles
from METdbLoad.ush.read_load_xml import XmlLoadFile
from write_stat_ascii import WriteStatAscii
from METcalcpy.metcalcpy.util.safe_log import safe_log
from METcalcpy.metcalcpy import logging_config
from METcalcpy.metcalcpy import scorecard
from METcalcpy.metcalcpy.agg_stat import AggStat


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
        os.makedirs(self.log_dir, exist_ok=True)
        self.log_filename = os.path.join(self.log_dir, configs['log_filename'])
        self.log_level = configs['log_level']
        self.logger = logging_config.setup_logging(configs)
        self.base_dir = configs['base_dir']
        self.image_dir = os.path.join(self.base_dir, 'METplotpy/metplotpy/plots/scorecard/images')

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

        self.get_all_statfiles = True

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

        # self.derived_series: list = configs['derived_series']
        self.derived_series: list[list] = self.create_derived_series()
        agg_fname = "aggstat_output.txt"
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

        # Plot-related
        self.base_dir = configs['base_dir']
        self.ci_map = self.get_category_images(self.base_dir)


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

        # Create a list of all the files in every directory
        all_files = []
        if self.get_all_statfiles:
            for curr_dir in final_list:
                for file in os.listdir(curr_dir):
                    if file.endswith(".stat"):
                        all_files.append(os.path.join(curr_dir, file))

        else:
            # Get the specific filenames by filename pattern
            print("Not yet implemented, retrieving all .stat files from each directory")

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

        # Create the Cartesian product of the above
        result = list(itertools.product(fcst_levs, models, fcst_leads, fcst_var, stats))

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


    def get_category_images(self, base_dir: str) -> dict:
        """
           Mapping of categories to their corresponding image.
           Join the source base directory to the METplotpy directory to get the
           full directory path.

           Args:
               base_dir (str): the directory that has the METplotpy source code

          Returns:
              a dictionary that maps the category to its corresponding image

        """

        ci_map = {
            'A999better': os.path.join(base_dir, 'METplotpy/metplotpy/plots/scorecard/images/large_green_tri.png'),
            'A99better': os.path.join(base_dir, 'METplotpy/metplotpy/plots/scorecard/images/small_green_tri.png'),
            'A95better': os.path.join(base_dir, 'METplotpy/metplotpy/plots/scorecard/images/green_square.png'),
            'A95worse': os.path.join(base_dir, 'METplotpy/metplotpy/plots/scorecard/images/pink_square.png'),
            'A99worse': os.path.join(base_dir, 'METplotpy/metplotpy/plots/scorecard/images/small_red_down.png'),
            'A999worse': os.path.join(base_dir, 'METplotpy/metplotpy/plots/scorecard/images/down_red.png'),
            'NOTSTATSIG': os.path.join(base_dir, 'METplotpy/metplotpy/plots/scorecard/images/gray_square.png'),
            'NOTRELEVANT': os.path.join(base_dir, 'METplotpy/metplotpy/plots/scorecard/images/blue_square.png')}

        return ci_map


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


    def subset_data(self, df_filename: str) -> pd.DataFrame:
        """
            Invoke this prior to invoking METcalcpy agg_stat.
            Subset data based on independent variable and its
            corresponding values, and any other columns in the data.
            This step eliminates the need for a database.

            Args:

                df filename (str): The filename of the  dataframe containing the MET stat data with
                                        all columns labelled

           Returns:
               result (pd.DataFrame): a dataframe after filtering/subsetting data based on criteria in the YAML config file
               Also saves a file that contains only the relevant information as specified in
               the YAML config file and also

        """
        safe_log(self.logger, 'debug', 'Filter data based on subset_params in the config file.')
        working_df = pd.read_csv(df_filename, sep='\t+', engine='python')
        working_df.to_csv(os.path.join(self.output_dir, "working.txt"), header=True, index_label=None, sep=',',
                          index=False, date_format="%Y-%m-%d %H:%M:%S")

        # Exit if there are any requested columns that don't exist in the data
        self.check_for_invalid_columns(working_df)

        # Replace the 'indep_variable' key with its value,
        # replace the 'indep_values' key with its values, and
        # replace stats_list keyname with stat_name
        filter_keys = self.subset_params
        indep_variable = filter_keys['indep_variable']
        indep_var_vals = filter_keys['indep_values']
        filter_keys[indep_variable] = indep_var_vals
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

        result.to_csv(self.subsetted_filename, sep='\t', header=True, index_label=False)
        return result


    def reformat_met_stat(self) -> None:
        """
             Invoke the METdataio METreformatter's write_stat_ascii module to
             label all the headers in the MET .stat file based on linetype (specified in
             the YAML config file).

             Args:

             Returns:
                 Saves the reformatted data  to the output
                 directory specified in the YAML config file.

        """

        if self.reformat_flag:
            r_df = self.read_input()
            r_df.to_csv(self.reformat_params['output_filename'],
                        date_format='%Y-%m-%d %H:%M:%S')
            if r_df.size == 0:
                safe_log(self.logger, 'ERROR', "ERROR:  Input dataframe is empty.  Exiting")
                sys.exit()
            if os.path.exists(self.reformat_params['output_filename']):
                safe_log(self.logger, self.log_level, "Output file already exists, removing this file.")
                os.remove(self.reformat_params['output_filename'])

            stat_lines_obj: WriteStatAscii = WriteStatAscii(self.reformat_params, self.logger)
            stat_lines_obj.write_stat_ascii(r_df, self.reformat_params)
        else:
            safe_log(self.logger, self.log_level, "Reformatting not requested")


    def calculate_agg_stats(self):
        """
            Calculate the CI's using METcalcpy agg_stat.py

        """
        fname = "reformatted_" + self.configs['linetype'] + ".txt"
        input_file = os.path.join(self.configs['output_dir'], fname)
        agg_stat_configs = {}

        # Generate the configuration settings needed by METcalcpy's agg_stat
        # module from the scorecard yaml config file.
        agg_stat_configs['agg_stat_input'] = input_file
        outname = self.configs['linetype'] + "_aggregated.data"
        agg_stat_configs['agg_stat_output'] = os.path.join(self.configs['output_dir'], outname )
        agg_stat_configs['alpha'] = 0.05
        agg_stat_configs['append_to_file'] = "null"
        agg_stat_configs['circular_block_bootstrap'] = True
        agg_stat_configs['derived_series_1'] = []
        agg_stat_configs['derived_series_2'] = []
        agg_stat_configs['event_equal'] = False

        # fcst_var_val_1 is the fcst_var and the stat (stat name is pre-fixed with
        # the linetype e.g. RMSE becomes ECNT_RMSE for linetype ECNT and
        # stat in the stat_list of the scorecard YAML).
        fcst_var = self.configs['subset_params']['fcst_var'][0]
        stats_list = self.configs['subset_params']['stats_name']

        # Pre-fix the linetype (upper case) to each stat name
        aggstat_stats = []
        # for stat in stats_list:
        #     aggstat_stats.append(str(self.configs['linetype']).upper() + "_" + stat)

        agg_stat_configs['fcst_var_val_1']= {fcst_var:aggstat_stats}
        agg_stat_configs['fcst_var_val_2'] = {}
        agg_stat_configs['indy_vals'] = self.configs['subset_params']['fcst_lead']
        agg_stat_configs['indy_var'] = 'fcst_lead'
        agg_stat_configs['line_type'] = str(self.configs['linetype']).lower()
        agg_stat_configs['list_stat_1'] = aggstat_stats
        agg_stat_configs['list_stat_2'] = []
        agg_stat_configs['method'] = 'perc'
        agg_stat_configs['num_iterations'] = 1
        agg_stat_configs['num_threads'] = -1
        agg_stat_configs['random_seed'] =  None
        agg_stat_configs['series_val_1'] = {'model':self.configs['subset_params']['model']}
        agg_stat_configs['series_val_2'] = []

        msg = "Calculating CI for "+ self.configs['linetype'] +" with agg_stat"
        safe_log(self.logger, self.log_level, msg)
        AGG_STAT = AggStat(agg_stat_configs)
        AGG_STAT.calculate_stats_and_ci()
        safe_log(self.logger, self.log_level, "Finished calculating CI with agg_stat")



    def get_scorecard_stats(self) -> pd.DataFrame:
        """
              Invoke the METcalcpy scorecard module to calculate the p-values.



              Args:

              Returns:
                 a dataframe that will be used to generate the
                 scorecard plot.

        """

        # Create the params expected by METcalcpy scorecard.py
        params = {}
        params['append_subsequent'] = self.append_sc_runs
        params['derived_series'] = self.derived_series
        params['ndays'] = self.sample_size
        params['pval_method'] = self.pval_method
        params['log_dir'] = self.log_dir
        params['log_filename'] = self.log_filename
        params['log_level'] = self.log_level
        params['scorecard_output'] = self.scorecard_stats_output_filename

        # ToDo put logic for whether agg stat was needed and use that output file
        # as input (CNT linetype does not require agg_stat.py, there are other linetypes
        # that also do not require agg_stat.py)
        if self.linetype == 'CNT':
            # use the reformatted output for scorecard stats input

            # remove the fcst_init_beg
            params['scorecard_input'] = self.subsetted_filename
        else:
            params['scorecard_input'] = self.aggstat_filename

        params['scorecard_output'] = self.scorecard_stats_output_filename
        params['series_val'] = self.scorecard_stats_series_val
        params['indy_var'] = self.scorecard_stats_indy_var
        params['indy_vals'] = self.scorecard_stats_indy_vals
        params['stats_list'] = self.scorecard_stats_statslist

        calcpy_sc = scorecard.Scorecard(params)
        calcpy_sc.calculate_scorecard_data()


    def categorize_scorecard_results(self) -> pd.DataFrame:
        """
           Categorize the scorecard results if the p-value was calculated via the
           'NCAR' method:

            Categorize each p-value into one of the following categories:
                   Model A better than Model B at 99.9% confidence
                   Model A better than Model B at 99% confidence
                   Model A better than Model B at 95% confidence

                   Model A worse than Model B at 95% confidence
                   Model A worse than Model B at 99% confidence
                   Model A worse than Model B at 99.9% confidence

                   No statistically significant difference between Model A and Model B
                   Not statistically relevant


           returns (pd.DataFrame): A dataframe containing the categorization value
                                               using the criteria in the METviewer scorecard

        """
        categories = {}
        categories['A_better_999'] = [0.999, 1.]
        categories['A_better_99'] = [0.99, 0.999]
        categories['A_better_95'] = [0.95, 0.99]
        categories['A_worse_999'] = [-1, -0.999]
        categories['A_worse_99'] = [-.999, -.99]
        categories['A_worse_95'] = [-.99, -.95]

        working_df = pd.read_csv(self.scorecard_stats_output_filename, sep="\t", engine="python")
        stat_values = working_df['stat_value']

        # Save the categorical values in a list
        categorized = []
        # Evaluate whether model A is better than model B
        for stat in stat_values:
            result = self.model_a_better(stat, categories)
            if result == 'NA':
                # Check if model A is worse than model B
                result = self.model_a_worse(stat, categories)
                if result == 'NA':
                    # Check for no statistical significance
                    result = self.no_statistical_significance(stat)
                    if result == 'NA':
                        # Not statistically relevant
                        result = 'NOTRELEVANT'
            categorized.append(result)

        # Add the categorized values to the scorecard dataframe
        categories: pd.Series = pd.Series(categorized)
        categorized_df = working_df.assign(category=categories)

        return categorized_df


    def model_a_better(self, stat, categories) -> str:
        """
            Determine if modelA (first model in config file) is better than modelB
            at the 99.9, 99, or 95% confidence levels.

            Args:
                stat_value (float): The p-value calculated by METcalcpy
                categories (dict): Categories employed in the METviewer scorecard

            Returns:
                    a string value if modelA is better than modelB.  One of these values
                      will be returned:
                      A999better
                      A99better
                      A95better
                      NA if modelA is not better than modelB

        """

        if stat >= categories['A_better_999'][0] and stat < categories['A_better_999'][1]:
            return "A999better"
        elif stat >= categories['A_better_99'][0] and stat < categories['A_better_99'][1]:
            return "A99better"
        elif stat >= categories['A_better_95'][0] and stat < categories['A_better_95'][1]:
            return "A95better"
        else:
            return "NA"


    def model_a_worse(self, stat, categories):
        """
                   Determine if modelA (the first model in the config file) is worse than
                   modelB at the 99.9, 99, or 95% confidence level.

                   Args:
                       stat_value (float): The p-value calculated by METcalcpy
                       categories (dict): Categories employed in the METviewer scorecard

                   Returns:
                      a string value if modelA is worse than modelB.  One of these values
                      will be returned:
                      A999worse
                      A99worse
                      A95worse
                      NA if modelA is not worse than modelB

               """
        if stat >= categories['A_worse_999'][0] and stat < categories['A_worse_999'][1]:
            return "A999worse"
        elif stat >= categories['A_worse_99'][0] and stat < categories['A_worse_99'][1]:
            return "A99worse"
        elif stat >= categories['A_worse_95'][0] and stat < categories['A_worse_95'][1]:
            return "A95worse"
        else:
            return "NA"


    def no_statistical_significance(self, stat) -> str:
        """
          Determine if the p-value indicates "no statistical significance" between
          modelA (first model in config) and modelB.

          Args:
          stat_value (float): the p-value calculated by METcalcpy

          Returns:
          a string value, one of the following:
                    NOTSTATSIG (if not statistically significant)
                    NA if not applicable
        """
        # Criteria for determining "not statistically significant", as used by the METviewer
        # scorecard
        min_val = -0.95
        max_val = 0.95
        if stat >= min_val and stat < max_val:
            return "NOTSTATSIG"
        else:
            return "NA"


    def generate_table(self, categorized_df: pd.DataFrame):
        """
        Generate the scorecard table/plot

        Args:
            categorized_df (pd.Dataframe): The dataframe with the p-values categorized

        Returns:
            None: Create a plot as a .png file

        """

        # Keep only relevant portions of the input dataframe
        columns_to_keep = ['fcst_lead', 'fcst_lev', 'fcst_var', 'stat_name', 'stat_value', 'category']
        scdf = categorized_df[columns_to_keep]

        # Rename the columns
        s = scdf.rename(columns={"fcst_var": "Variable", 'fcst_lev': 'Level', 'stat_name': 'Stat', 'fcst_lead': 'HmS',
                                 'category': 'category'})

        # Substitute the category text with images
        scdf['category'] = scdf['category'].map(self.ci_map)
        scdf_img = scdf.copy()
        print(f"scdf with images: {scdf_img}")
        # Plottable column definitions
        coldefs = [
            ColumnDefinition(name="Stat",
                             textprops={"ha": "right"},
                             width=0.5,
                             ),
            ColumnDefinition(name=" Variable",
                             textprops={"ha": "center"},
                             width=1.5,
                             ),
            ColumnDefinition(name=" Level",
                             textprops={"ha": "center"},
                             width=1.5,
                             ),
            ColumnDefinition(name=" HmS",
                             textprops={"ha": "center"},
                             width=1.5,
                             ),
            ColumnDefinition(name="category",
                             textprops={"ha": "right"},
                             width=1.5, plot_fn=image
                             ),
        ]

        fig, ax = plt.subplots(figsize=(8, 7))
        print("creating table")
        table = Table(
            scdf_img,
            column_definitions=coldefs,
            ax=ax,
            textprops={"fontsize": 12},
            row_divider_kw={"linewidth": 5, "linestyle": (0, (1, 5))},
            col_label_divider_kw={"linewidth": 2, "linestyle": "-"},
            column_border_kw={"linewidth": 11, "linestyle": "-"},

        )

        # Adding the bold header as a text annotation using \n to create a new line
        print("adding header")
        header_text = "\n Scorecard HRRR, RRFS"
        header_props = {'fontsize': 18, 'fontweight': 'bold', 'va': 'center', 'ha': 'center', 'color': 'red'}
        # Adjusting the y-coordinate to bring the header closer to the table
        plt.text(0.5, 0.91, header_text, transform=fig.transFigure, **header_props)

        # Adding the subtitle at the top in gray
        print("adding subtitle")
        subtitle_text = "\n for HRRR and RRFS \n20230701 00:0000 \n 20230704 00:00:00 \n  "
        subtitle_props = {'fontsize': 8, 'va': 'center', 'ha': 'center', 'color': 'gray'}
        # plt.rcParams['axes.titley'] = 1.0    # y is in axes-relative coordinates.
        # plt.rcParams['axes.titlepad'] = -14  # pad is in points...
        plt.text(0.5, 0.8, subtitle_text, transform=fig.transFigure, **subtitle_props)

        print("saving plot")
        plt.savefig("/Users/minnawin/Python_Scorecard_Dev/output/scorecard_plot.png")
        plt.show()


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
    sc.reformat_met_stat()
    #
    #  Filter the data based on settings in the YAML config file
    #
    sc.subset_data(sc.reformat_params['output_filename'])

    #
    # Calculate the aggregation statistics via METcalcpy agg_stat.py
    # module if needed
    if confs['has_confidence_stats']:
        print(f"Skip running agg_stat.py {sc.linetype} already has CI's calculated  ")
    else:
        print(f" Invoke  METcalcpy agg_stat.py to calculate the CI's for {sc.linetype} ")
        sc.calculate_agg_stats()
        sys.exit()


    #
    # Get the p-values and scorecard categories
    #

    # input is dependent on whether agg_stat.py was used to calculate the CI's
    # CNT line type already has CI's

    _: pd.DataFrame = sc.get_scorecard_stats()

    # Categorize the p-values
    # Open the scorecard output from METcalcpy scorecard.py and
    # assign the categories (based on the categories used in METviewer)
    if sc.pval_method == 'NCAR':
        cat_df: pd.DataFrame = sc.categorize_scorecard_results()
        cat_df.to_csv("/Users/minnawin/Python_Scorecard_Dev/output/categorized.txt", index=False, header=True)

    # Generate the scorecard as a table using plottable
    sc.generate_table(cat_df)


if __name__ == "__main__":
    # print("Scorecard plotting")
    # datafile = "/Users/minnawin/Python_Scorecard_Dev/METcalcpy/metcalcpy/output/hrrr_rrfs_output.data"
    # main(datafile)
    main()
