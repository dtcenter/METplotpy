"""
Module Name: constants.py

Mapping of constants used in plotting, as dictionaries.
METviewer values are keys, Matplotlib representations are the values.

"""
__author__ = 'Minna Win'
__email__ = 'met_help@ucar.edu'


# Available Matplotlib Line styles
# ':'  ...
# '-.'  _._.
# '--'  -----
# '-'   ______ (solid line)
# ' '   no line

# METviewer drop-down choices:
# p points  (...)
# l lines   (---, dashed line)
# o overplotted (_._ mix of dash and dots)
# b joined lines (____ solid line)
# s stairsteps  (same as overplotted)
# h histogram like (no line style, this is unsupported)
# n none (no line style)

LINESTYLE_DICT = {'p': ':', 'l': '--', 'o': '-.', 'b': '-',
                  's': '-.', 'h': ' ', 'n': ' '}


ACCEPTABLE_CI_VALS = ['NONE', 'BOOT', 'NORM']

DEFAULT_TITLE_FONT = 'sans-serif'
DEFAULT_TITLE_COLOR = 'darkblue'
DEFAULT_TITLE_FONTSIZE = 10
# Default size used in plotly legend text
DEFAULT_LEGEND_FONTSIZE = 12
AVAILABLE_MARKERS_LIST = ["o", "^", "s", "d", "H", "."]

