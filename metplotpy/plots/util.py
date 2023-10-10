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
import sys
import getpass
import logging
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
    parser = argparse.ArgumentParser(description='Generates a performance diagram')

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

def is_thresh_column(column_name:str)->bool:
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


def create_query(input_df:pd.DataFrame, settings_dict: dict) -> str:

    """
        Create a query string to filter the input dataframe, based on the
        settings provided in the YAML file.  These settings are represented
        by the settings_dict dictionary.

        Args:
           input_df: The input dataframe to be subset.  This is needed to check for
                     valid columns.
           settings_dict: The dictionary representation of the settings in the YAML
           configuration file

        Returns:
           df_query_string: The query string to provide to the pd.query() method
    """

    # check if columns (keys) in fixed_vars_vals_dict exist in the dataframe before
    # attempting to subset
    valid_columns = [col for col in settings_dict if col in input_df.columns]

    # Use the valid columns to create the query string in the format:
    # col_a in ('x', 'y', 'z') and col_b in ('a', 'b', 'c')
    # where the items in the parenthesis represent the list of
    # values associated with a particular column (e.g. col_a, col_b).
    query_string = ''
    prev_query_string = ''
    val_string = ''
    prev_val_string = ''

    for idx, col in enumerate(valid_columns):
        # Identify when we've reached the last
        # column so we don't add an extraneous
        # '&' at the end of the query.
        last_col = idx + 1
        prev_val_string = ''
        single_quote = "'"
        list_sep = "', "
        in_token = " in ("
        list_terminator = ')'
        and_token = ') &'
        values = settings_dict[col]
        query_string = col + ' in ('
        for val_idx, val in enumerate(values):
            # Identify when the last value in the list
            # has been reached to avoid adding a ',' after
            # the last value.
            last_val = val_idx + 1

            if last_val == len(values):
                val_string = single_quote + val + single_quote
            else:
                val_string = single_quote + val + list_sep
            val_string = prev_val_string + val_string
            prev_val_string = val_string
        if last_col == len(valid_columns):
            query_string = col + in_token + val_string + list_terminator
        else:
            # Adding the & in between each "col in list"
            query_string = col + in_token + val_string + and_token

        query_string = prev_query_string + query_string
        prev_query_string = query_string
    df_query_string = prev_query_string

    return df_query_string
