import os, sys
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from metplotpy.external.plottable import plottable
from metplotpy.external.plottable.plottable import Table
from metplotpy.external.plottable.plottable import ColumnDefinition
from metplotpy.external.plottable.plottable.cmap import normed_cmap
from metplotpy.external.plottable.plottable.plots import image
from metplotpy.plots import util as plot_util
from metplotpy.plots import config as mp_config
import METdataio.METreformat.write_stat_ascii as reformat
from METcalcpy.metcalcpy.util.safe_log import safe_log
from METcalcpy.metcalcpy import logging_config
from write_stat_ascii import WriteStatAscii


class ScorecardPlot():
    def __init__(self, configs):
        # Assign the instance attributes based on config file settings
        self.configs = configs

        # Logging and output location contain information for
        # all steps
        self.output_dir = configs['output_dir']
        os.makedirs(self.output_dir, exist_ok=True)
        self.log_dir = configs['log_dir']
        os.makedirs(self.log_dir, exist_ok=True)
        self.log_filename = os.path.join(self.log_dir, configs['log_filename'])
        self.log_level = configs['log_level']
        self.logger = logging_config.setup_logging(configs)

        logger = self.logger
        safe_log(logger, "debug", "Initializing ScorecardPlot with parameters")

        # For reformatter
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

        # For subsetting
        # self.indep_values: list = configs['indep_values']
        # self.indep_variable: str = configs['indep_variable']
        # self.statistics: list = configs['stats_list']
        self.subset_params: dict = configs['subset_params']

        self.append_sc_runs: bool = configs['append_subsequent']
        self.derived_series: list[list] = configs['derived_series']
        # num of days, used in bootstrapping
        self.ndays = int(configs['ndays'])
        self.pval_method: str = configs['pval_method']

        # Plot-related TBD


    def __repr__(self):

        class_name = type(self).__name__
        return (f"{class_name}(config={self.configs!r},)"
                )


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


    def subset_data(self, df_filename: str) -> None:
        """
            Invoke this prior to invoking METcalcpy agg_stat.
            Subset data based on independent variable and its
            corresponding values, and any other columns in the data.
            This step eliminates the need for a database.

            Args:

                df filename (str): The filename of the  dataframe containing the MET stat data with
                                        all columns labelled

           Returns:
               a dataframe that contains only the relevant information as specified in
               the YAML config file

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
                if column_name == 'fcst_lead' :
                    query_token = f' ({column_name} == {cur_value} )'
                else:
                    query_token =  f' ({column_name} == "{cur_value}" )'

                # Add the 'OR' logic operator
                # between each value corresponding to this column
                if len(values) > 1 and idx_val != idx_last_value:
                    query_token =  query_token + ' | '
                queries_by_column.append(query_token)
            all_queries_for_this_column = ''.join(queries_by_column)
            all_queries_by_cols[column_name] = all_queries_for_this_column

        # Add the appropriate parens and the 'AND'
        # logical operator between the query tokens based on column
        all_columns = all_queries_by_cols.keys()
        last_column = len(all_columns) -1
        for idx, cur_col in enumerate(all_columns):
            values_for_col = all_queries_by_cols[cur_col]

            if idx != last_column:
                values_for_col_updated = "(" + values_for_col + " ) & "
            else:
                values_for_col_updated = "(" + values_for_col + " ) "

            # Add this to the "all queries" dictionary
            all_queries_by_cols[cur_col] = values_for_col_updated


        # Create the full query string
        full_query_str_list = []
        for v in all_queries_by_cols.values():
             # only collect the values into a list to be joined later to create the full query
             full_query_str_list.append(v)

        full_query =  "".join(full_query_str_list)

        result: pd.DataFrame  = working_df.query(full_query)

        # ToDo
        # Remove only to DEBUG
        result.to_csv("/Users/minnawin/Python_Scorecard_Dev/filtered.csv", header=True, index_label=False)


        return result



    def insert_char(self, input_string:str, char_to_insert:str, location:int) -> str:
        """
             Insert a character into a string at a specified index

             Args:
                 input_str (str): the string to add a character to
                 char_to_insert (str): the character to add to the string
                 location (int): the location (index) indicating where to
                 insert the character r

             Returns:
                  a new string with the inserted char

        """

        return f"{input_string[:location]}{char_to_insert}{input_string[location:]}"




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
    # Reformat the MET stat data
    #
    if sc.reformat_flag:
        r_df = reformat.read_input(sc.reformat_params, sc.logger)
        r_df.to_csv('/Users/minnawin/Python_Scorecard_Dev/output/before_reformatter.txt',
                    date_format='%Y-%m-%d %H:%M:%S')
        if r_df.size == 0:
            safe_log(sc.logger, 'ERROR', "ERROR:  Input dataframe is empty.  Exiting")
            sys.exit()
        if os.path.exists(sc.reformat_params['output_filename']):
            safe_log(sc.logger, sc.log_level, "Output file already exists, removing this file.")
            os.remove(sc.reformat_params['output_filename'])

        stat_lines_obj: WriteStatAscii = WriteStatAscii(sc.reformat_params, sc.logger)
        stat_lines_obj.write_stat_ascii(r_df, sc.reformat_params)

    #
    #  Filter the data based on settings in the YAML config file
    #
    subset_df = sc.subset_data(sc.reformat_params['output_filename'])


    # Calculate the aggregation statistics via METcalcpy agg_stat.py
    # module
    if sc.linetype != 'CNT':
        print(f"Calculate CI's with agg_stat for {sc.linetype} ")

    # Calculate the p-values


    # Categorize the p-values

    # Generate the scorecard as a table using plottable


if __name__ == "__main__":
    # print("Scorecard plotting")
    # datafile = "/Users/minnawin/Python_Scorecard_Dev/METcalcpy/metcalcpy/output/hrrr_rrfs_output.data"
    # main(datafile)
    main()
