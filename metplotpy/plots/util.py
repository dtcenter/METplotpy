import argparse

"""
    Collection of utility functions used by multiple plotting classes
"""
__author__ = 'Minna Win'

import matplotlib
import numpy as np
from typing import Union

from plotly.graph_objects import Figure


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
    Compute a sequence of about n+1 equally spaced ‘round’ values which cover the range of the values in x
    Can be used  to create axis labels or bins
    :param low: min value
    :param high: max value
    :param number_of_intervals: number of intervals
    :return:
    """
    if number_of_intervals == 1:
        return [-1, 0]

    range = nicenumber(high - low, False)
    d = nicenumber(range / (number_of_intervals - 1), True)
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
