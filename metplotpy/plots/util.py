# ============================*
# ** Copyright UCAR (c) 2020
# ** University Corporation for Atmospheric Research (UCAR)
# ** National Center for Atmospheric Research (NCAR)
# ** Research Applications Lab (RAL)
# ** P.O.Box 3000, Boulder, Colorado, 80307-3000, USA
# ============================*


"""
    Collection of utility functions used by multiple plotting classes
"""
__author__ = 'Minna Win'

import argparse
from typing import Tuple
import sys
import getpass
import logging
import gc
import re
import matplotlib
import numpy as np
from typing import Union
import pandas as pd
from plotly.graph_objects import Figure
from metplotpy.plots.context_filter import ContextFilter as cf

COLORSCALES = {
    'green_red': ['#E6FFE2', '#B3FAAD', '#74F578', '#30D244', '#00A01E', '#F6A1A2',
                  '#E26667', '#C93F41', '#A42526'],
    'blue_white_brown': ['#1962CF', '#3E94F2', '#B4F0F9', '#00A01E', '#4AF058',
                         '#C7FFC0', '#FFFFFF', '#FFE97F',
                         '#FF3A20', '#A50C0F', '#E1BFB5', '#A0786F', '#643D34'],
    'cm_colors': ["#80FFFF", "#95FFFF", "#AAFFFF", "#BFFFFF", "#D4FFFF", "#EAFFFF",
                  "#FFFFFF", "#FFEAFF", "#FFD5FF",
                  "#FFBFFF", "#FFAAFF", "#FF95FF", "#FF80FF"],
    'topo_colors': ["#4C00FF", "#0000FF", "#004CFF", "#0099FF", "#00E5FF", "#00FF4D",
                    "#1AFF00", "#80FF00", "#E6FF00",
                    "#FFFF00", "#FFE53B", "#FFDB77", "#FFE0B3"],
    'terrain_colors': ["#00A600", "#24B300", "#4CBF00", "#7ACC00", "#ADD900", "#E6E600",
                       "#E7CB21", "#E9BA43",
                       "#EBB165", "#EDB387", "#EFBEAA", "#F0D3CE", "#F2F2F2"],
    'heat_colors': ["#FF0000", "#FF1C00", "#FF3900", "#FF5500", "#FF7100", "#FF8E00",
                    "#FFAA00", "#FFC600", "#FFE300",
                    "#FFFF00", "#FFFF2A", "#FFFF80", "#FFFFD5"],
    'rainbow': ["#FF0000", "#FF7600", "#FFEB00", "#9DFF00", "#27FF00", "#00FF4E",
                "#00FFC4", "#00C4FF", "#004EFF",
                "#2700FF", "#9D00FF", "#FF00EB", "#FF0076"]
}


def read_config_from_command_line():
    """
        Read the "custom" config file from the command line

        Args:

        Returns:
            The full path to the config file
    """
    # Create Parser
    parser = argparse.ArgumentParser(description='Read in config file')

    # Add arguments
    parser.add_argument('Path', metavar='path', type=str,
                        help='the full path to config file')

    # Execute the parse_args() method
    args = parser.parse_args()
    return args.Path


def alpha_blending(hex_color: str, alpha: float) -> str:
    """ Alpha color blending as if on the white background.
        Useful for gridlines

    Args:
        @param hex_color - the color in hex
        @param alpha - Alpha value between 0 and 1
    Returns: blended hex color
    """
    foreground_tuple = matplotlib.colors.hex2color(hex_color)
    foreground_arr = np.array(foreground_tuple)
    final = tuple((1. - alpha) + foreground_arr * alpha)
    return matplotlib.colors.rgb2hex(final)


def apply_weight_style(text: str, weight: int) -> str:
    """
    Applied HTML style weight to text:
    1 - none
    2 - bold
    3 - italic
    4 - bold italic

    :param text: text to style
    :param weight: - int representation of the style
    :return: styled text
    """
    if len(text) > 0:
        if weight == 2:
            return '<b>' + text + '</b>'
        if weight == 3:
            return '<i>' + text + '</b>'
        if weight == 4:
            return '<b><i>' + text + '</i></b>'
    return text


def nicenumber(x, to_round):
    """
    Calculates a close nice number, i. e. a number with simple decimals.
    :param x: A number
    :param to_round: Should the number be rounded?
    :return: A number with simple decimals
    """
    exp = np.floor(np.log10(x))
    f = x / 10 ** exp

    if to_round:
        if f < 1.5:
            nf = 1.
        elif f < 3.:
            nf = 2.
        elif f < 7.:
            nf = 5.
        else:
            nf = 10.
    else:
        if f <= 1.:
            nf = 1.
        elif f <= 2.:
            nf = 2.
        elif f <= 5.:
            nf = 5.
        else:
            nf = 10.

    return nf * 10. ** exp


def pretty(low, high, number_of_intervals) -> Union[np.ndarray, list]:
    """
    Compute a sequence of about n+1 equally spaced ‘round’ values which cover the
    range of the values in x
    Can be used  to create axis labels or bins
    :param low: min value
    :param high: max value
    :param number_of_intervals: number of intervals
    :return:
    """
    if number_of_intervals == 1:
        return [-1, 0]

    num_range = nicenumber(high - low, False)
    d = nicenumber(num_range / (number_of_intervals - 1), True)
    miny = np.floor(low / d) * d
    maxy = np.ceil(high / d) * d
    return np.arange(miny, maxy + 0.5 * d, d)


def add_horizontal_line(figure: Figure, y: float, line_properties: dict) -> None:
    """
    Adds a horizontal line to the Plotly Figure
    :param figure: Plotly plot to add a line to
    :param y: y value for the line
    :param line_properties: dictionary with line properties like color, width, dash
    :return:
    """
    figure.add_shape(
        type='line',
        yref='y', y0=y, y1=y,
        xref='paper', x0=0, x1=1,
        line=line_properties,
    )


def add_vertical_line(figure: Figure, x: float, line_properties: dict) -> None:
    """
    Adds a vertical line to the Plotly Figure
    :param figure: Plotly plot to add a line to
    :param x: x value for the line
    :param line_properties: dictionary with line properties like color, width, dash
    :return:
    """
    figure.add_shape(
        type='line',
        yref='paper', y0=0, y1=1,
        xref='x', x0=x, x1=x,
        line=line_properties,
    )


def abline(x_value: float, intercept: float, slope: float) -> float:
    """
    Calculates y coordinate based on x-value, intercept and slope
    :param x_value: x coordinate
    :param intercept:  intercept
    :param slope: slope
    :return: y value
    """
    return slope * x_value + intercept


def is_threshold_value(values: Union[pd.core.series.Series, list]):
    """
    Determines if a pandas Series of values are threshold values (e.g. '>=1', '<5.0',
    '>21')

    Args:
       @param values:  pandas Series of independent variables comprising the x-axis

    Returns:
    A tuple of boolean values:
    True if any of these values is a threshold (ie. operator and number) and True if
    these are mixed threshold
    (==SFP50,==FBIAS1, etc. ). False otherwise.

    """

    thresh_ctr = 0
    percent_thresh_ctr = 0
    is_percent_thresh = False
    is_thresh = False
    # Check all the threshold values, there may be some threshold values that do not
    # have an equality operator when equality is implied.
    for cur_value in values:
        match_pct = re.match(
            r'(\<|\<=|\==|\>=|\>)(\s)*(SFP|SOP|SCP|USP|CDP|FBIAS)(\s)*([+-]?([0-9]*['
            r'.])?[0-9]+)',
            str(cur_value))
        match_thresh = re.match(r'(\<|\<=|\==|\>=|\>)(\s)*([+-]?([0-9]*[.])?[0-9]+)',
                                str(cur_value))
        if match_pct:
            # This is a percent threshold, with values like '==FBIAS1'.
            percent_thresh_ctr += 1
        elif match_thresh:
            thresh_ctr += 1

    if thresh_ctr >= 1:
        is_thresh = True
    if percent_thresh_ctr >= 1:
        is_percent_thresh = True

    return is_thresh, is_percent_thresh


def sort_threshold_values(thresh_values: pd.core.series.Series) -> list:
    """
    Sort the threshold values based on operator and numerical value

    Args:
        @param thresh_values: a pandas Series of threshold values (operator + number)

    Return:
       sorted_thresholds: A list of threshold values as strings (operator+numerical
       value)
    """

    operators = []
    values = []
    for cur_val in thresh_values:
        # treat the thresh value as comprised of two groups, one
        # for the operator and the other for the value (which can be a
        # negative value)
        match = re.match(r'(\<|\<=|\==|\>=|\>)(\s)*([+-]?([0-9]*[.])?[0-9]+)',
                         str(cur_val))
        if match:
            operators.append(match.group(1))
            value = float(match.group(3))
            values.append(value)
        else:
            # This is a bare number (float or int)
            operators.append(None)
            values.append(float(cur_val))

    # Apply weights to the operators
    wt_maps = {'<': 1, '<=': 2, '==': 3, '>=': 4, '>': 5}
    wts = []

    for operator in operators:
        # assign weight for == if no
        # operator is indicated, assuming
        # that a fcst_thresh of 5 is the same as
        # ==5
        # otherwise, assign the appropriate weight to
        # the operator
        if operator is None:
            wts.append(3)
        else:
            wts.append(wt_maps[operator])

    # Create a pandas dataframe to use the ability to sort by multiple columns
    thresh_dict = {'thresh': thresh_values, 'thresh_values': values, 'op_wts': wts}
    df = pd.DataFrame(thresh_dict)

    # cols is the list of columns upon which we should sort
    twocols = ['thresh_values', 'op_wts']
    sorted_val_wt = df.sort_values(by=twocols, inplace=False, ascending=True,
                                   ignore_index=True)

    # now the dataframe has the xyz_thresh values sorted appropriately
    return sorted_val_wt['thresh']


def get_common_logger(log_level, log_filename):
    '''
      Args:
         @param log_level:  The log level
         @param log_filename: The full path to the log file + filename
      Returns:
         common_logger: the logger common to all the METplotpy modules that are
                        currently in use by a plot type.
    '''

    # Supported log levels.
    log_level = log_level.upper()
    log_levels = {'DEBUG': logging.DEBUG, 'INFO': logging.INFO,
                  'WARNING': logging.WARNING, 'ERROR': logging.ERROR,
                  'CRITICAL': logging.CRITICAL}

    if log_filename.lower() == 'stdout':
        logging.basicConfig(level=log_levels[log_level],
                            format='%(asctime)s||User:%('
                                   'user)s||%(funcName)s|| [%(levelname)s]: %('
                                   'message)s',
                            datefmt='%Y-%m-%d %H:%M:%S',
                            stream=sys.stdout)
    else:

        logging.basicConfig(level=log_levels[log_level],
                            format='%(asctime)s||User:%('
                                   'user)s||%(funcName)s|| [%(levelname)s]: %('
                                   'message)s',
                            datefmt='%Y-%m-%d %H:%M:%S',
                            filename=log_filename,
                            filemode='w')
    mpl_logger = logging.getLogger(name='matplotlib').setLevel(logging.CRITICAL)
    common_logger = logging.getLogger(__name__)
    f = cf()
    common_logger.addFilter(f)

    return common_logger


def is_thresh_column(column_name: str) -> bool:
    '''
       Determines if a column is a threshold column, i.e. cov_thresh, fcst_thresh,
       or obs_thresh.

       Args:

       @param column_name:  A string representation of the column name

       Returns: True if this column is a threshold column, False otherwise
    '''

    match = re.match(r'.*_thresh.*', column_name)
    if match:
        return True
    else:
        return False


def filter_by_fixed_vars(input_df: pd.DataFrame, settings_dict: dict) -> pd.DataFrame:

    """
        Filter the input data based on values in the settings_dict dictionary.
        For each key (corresponding to a column in the input_df dataframe),
        create a query string.  Use that query string to filter the input dataframe.
        Repeat for all the keys and their corresponding values in the settings_dict.

        Use the pandas query() to perform database-like syntax for filtering the data:
            col in ('a', 'b', '3', ...,'z')

            where col is the name of the key and the values in the parens represent
            the values corresponding to that key.

        Since Python handles nan values in an unexpected way, if 'NA' is a value in the
        list of values corresponding to a key, then different syntax will be required:

             col.isnull() | col in ('a', 'b', ..., 'z')

        Args:
           input_df: The input dataframe to be subset.  This is needed to check for
                     valid columns.
           settings_dict: The dictionary representation of the settings in the YAML
           configuration file

        Returns:
           filtered_df:  The filtered dataframe
    """

    # check if columns (keys) in the settings_dict exist in the dataframe before
    # attempting to subset.  If the settings_dict has keys that do not have
    # corresponding column values in the dataframe, return the input dataframe.
    valid_columns = [col for col in settings_dict if col in input_df.columns]

    if len(valid_columns) == 0:
        print(
            "No columns in data match what is requested.  Input dataframe will be "
            "returned")
        return input_df

    # The pandas query method does not work as expected if
    # one of the values in the list is 'NA'. When 'NA' is an element in the list
    # use the col.isnull() syntax with the col in ('a', 'b', ..., 'z') syntax
    # for the remaining values.

    # Create a query string for each column and save in a list
    query_string_list = []

    # Use an intermediate dataframe for filtering iteratively by column
    filtered_df = input_df.copy(deep=True)

    for idx, col in enumerate(valid_columns):
        # Variables for creating the query string
        prev_val_string = ""
        single_quote = "'"
        list_sep = ", "
        list_start = "("
        list_terminator = ")"
        or_token = "| "
        in_token = " in "
        isnull_token = ".isnull()"
        is_last_val = False
        na_found = False
        updated_vals = []

        # Remove NA from the list of values and create a new
        # list of values containing the remaining non-NA values.
        values = settings_dict[col]
        for val in values:
            if val == 'NA':
                na_found = True
            else:
                updated_vals.append(val)

        # Create the query string based on whether or not there is/are NA values.
        if na_found:
            if len(updated_vals) == 0:
                # NA was the only value for this column, create the query
                # then move onto the next column
                prev_val_string = col + isnull_token
                query_string_list.append(prev_val_string)

            else:
                # At least one non-NA value in the list of values
                prev_val_string = col + isnull_token + or_token
                is_last_val = False
                # Build remaining portion of the query (ie the col in ('a', 'b',
                # 'c'))
                for val_idx, val in enumerate(updated_vals):
                    # Identify when the last value in the list
                    # has been reached to avoid adding a ',' after
                    # the last value.
                    last_val = val_idx + 1

                    if last_val == len(updated_vals):
                        is_last_val = True

                    #  Create the 'col in' portion of the query
                    if val_idx == 0 and is_last_val:
                        # Both the first and last element in the list (i.e. list of one
                        # element)
                        prev_val_string = prev_val_string + col + in_token + \
                                          list_start + single_quote + val + \
                                          single_quote + list_terminator

                    elif val_idx == 0 and (not is_last_val):
                        # First value of a list of values
                        prev_val_string = prev_val_string + col + in_token + \
                                          list_start + single_quote + val + \
                                          single_quote + list_sep



                    elif val_idx > 0 and not is_last_val:
                       # One of the middle values in the list
                       query_string = prev_val_string + single_quote + val + \
                                      single_quote + list_sep

                    else:
                        # The last value in the list
                        prev_val_string = prev_val_string + single_quote + val + \
                                          single_quote + list_terminator

                query_string_list.append(prev_val_string)


        else:

            # No NA's found in values. Create the query: col in ('a', 'b', 'c')
            prev_val_string = ""
            is_last_val = False

            for val_idx, val in enumerate(updated_vals):

                # Identify when the last value in the list
                # has been reached to avoid adding a ',' after
                # the last value.
                last_val = val_idx + 1

                if last_val == len(updated_vals):
                    is_last_val = True

                # Only one value in the values list (both first and last element)
                if val_idx == 0 and is_last_val:
                    prev_val_string = prev_val_string + col + in_token + list_start\
                                      + single_quote + val + single_quote +\
                                      list_terminator

                elif val_idx == 0 and (not is_last_val):
                    # First value of a list of values
                    prev_val_string = prev_val_string + col + in_token +\
                                      list_start + single_quote + val +\
                                      single_quote + list_sep

                elif val_idx > 0 and not is_last_val:
                    # One of the middle values in the list
                    prev_val_string = prev_val_string + single_quote + val + single_quote + list_sep
                else:
                    # Last value in the list
                    prev_val_string = prev_val_string + single_quote + val + single_quote + list_terminator

            query_string_list.append(prev_val_string)


    # Perform query for each column (key)
    for cur_query in query_string_list:
        working_df = filtered_df.query(cur_query)
        filtered_df = working_df.copy(deep=True)


    #  clean up
    del working_df
    gc.collect()

    return filtered_df
