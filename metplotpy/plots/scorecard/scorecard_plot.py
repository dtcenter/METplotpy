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
        linetype = str(configs['linetype'])
        self.reformat_flag = configs['reformat_needed']
        self.reformat_params = {}
        self.reformat_params['input_stats_aggregated'] = configs['has_confidence_stats']
        self.reformat_params['log_directory'] = self.log_dir
        self.reformat_params['output_dir'] = self.output_dir
        reformat_output_fname_parts = ["reformatted_", linetype, ".txt"]
        reformat_output_fname = ''.join(reformat_output_fname_parts)
        self.reformat_params['output_filename'] = os.path.join(self.output_dir, reformat_output_fname)
        self.reformat_params['input_data_dir'] = configs['met_stat_input']
        self.reformat_params['log_directory'] = self.log_dir
        self.reformat_params['log_filename'] = self.log_filename
        self.reformat_params['log_level'] = self.log_level
        self.reformat_params['line_type'] = linetype

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
                          index=False)
        # print(f" subset_params: {self.subset_params}")

        # Retrieve all the column names in the data frame:
        all_cols = working_df.columns.to_list()

        self.check_for_invalid_columns(working_df)

        filter_keys = self.subset_params

        # Create queries for column names specified in the subset_params settings.
        # 'OR' all the values corresponding to each key, and 'AND' all of the
        # key "segments" to create a final query.

        query = []
        idx_last_key = len(filter_keys) - 1
        query.append("' ")

        for idx, filter_key in enumerate(filter_keys):
            # Get the values for the current filter key
            values = self.subset_params[filter_key]
            idx_last_value = len(values) - 1

            for idx_val, cur_value in enumerate(values):
                # Group the 'OR' appropriately with external parens
                if idx_val == 0:
                    # Add the outermost left parens to separate this key's values
                    # from other keys' values
                    query_str = "((" + f"{filter_key} == {cur_value}  )"
                elif idx_val == idx_last_value:
                    query_str = "(" + f"{filter_key} == {cur_value}  ))"
                else:
                    query_str = "(" + f"{filter_key} == {cur_value}  )"

                # Apply the 'OR' in between each key-value statement
                if idx_val != idx_last_value:
                    query_str = query_str + "  |  "
                elif idx != idx_last_key:
                    # Append the 'AND' between this last value for this key and
                    # the next key's values
                    query_str = query_str + " & "

                query.append(query_str)

            if idx == idx_last_key:
                # Add the terminating right single quote to the query
                query.append("'")

        final_query_str = ''.join(query)
        msg = "Query string: " + final_query_str
        safe_log(self.logger, 'debug', msg)
        print(f"final query: {final_query_str}")
        # result_df = working_df.query('((fcst_lead== 0) | ( fcst_lead == 60000) | ( fcst_lead== 120000) | ( fcst_lead == 240000)) & (fcst_lev== "Z2") & (model=="HRRR_verification_mem000") & (fcst_init_beg=="2023-07-02 00:00:00")')
        # print(f"result: {result_df.shape}")
        # result_df.to_csv("/Users/minnawin/Python_Scorecard_Dev/output/query_result.txt", header=True, index_label=False, sep=",")

        # Create queries for the independent variable and its
        # corresponding value(s), and requested statistics

        # return working_df


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

    # Subset the reformatted data based on the subset_params

    # Calculate the aggregation statistics via METcalcpy agg_stat.py
    # module

    # Calculate the p-values

    # Categorize the p-values

    # Generate the scorecard as a table using plottable


if __name__ == "__main__":
    # print("Scorecard plotting")
    # datafile = "/Users/minnawin/Python_Scorecard_Dev/METcalcpy/metcalcpy/output/hrrr_rrfs_output.data"
    # main(datafile)
    main()
