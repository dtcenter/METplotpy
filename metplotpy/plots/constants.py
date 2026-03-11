# ============================*
 # ** Copyright UCAR (c) 2020
 # ** University Corporation for Atmospheric Research (UCAR)
 # ** National Center for Atmospheric Research (NCAR)
 # ** Research Applications Lab (RAL)
 # ** P.O.Box 3000, Boulder, Colorado, 80307-3000, USA
 # ============================*
 
 
 
"""
Module Name: constants.py

Mapping of constants used in plotting, as dictionaries.
METviewer values are keys, Matplotlib representations are the values.

"""
__author__ = 'Minna Win'

# CONVERSION FACTORS

# used to convert plot units in mm to
# inches, so we can pass in dpi to matplotlib
MM_TO_INCHES = 0.03937008
CM_TO_INCHES = MM_TO_INCHES * 0.1

PIXELS_TO_POINTS = 0.72

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

# linestyles can be indicated by "long" name (points, lines, etc.) or
# by single letter designation ('p', 'n', etc)
LINESTYLE_BY_NAMES = {'solid': '-', 'points': ':', 'lines': '--', 'overplotted': '-.',
                      'joined lines': '-', 'stairstep': '-.',
                      'histogram': ' ', 'none': ' ', 'p': ':',
                      'l': '--', 'o': '-.', 'b': '-',
                      's': '-.', 'h': ' ', 'n': ' '}

ACCEPTABLE_CI_VALS = ['NONE', 'BOOT', "STD", 'MET_PRM', 'MET_BOOT']

DEFAULT_TITLE_FONT = 'sans-serif'
DEFAULT_TITLE_COLOR = 'black'
DEFAULT_TITLE_FONTSIZE = 10

# Default size used in plotly legend text
DEFAULT_LEGEND_FONTSIZE = 12
DEFAULT_CAPTION_FONTSIZE = 14
DEFAULT_CAPTION_Y_OFFSET = 0.01
DEFAULT_TITLE_FONT_SIZE = 11
DEFAULT_TITLE_OFFSET = 0.02


AVAILABLE_MARKERS_LIST = ["o", "^", "s", "d", "H", ".", "h"]

PCH_TO_MATPLOTLIB_MARKER = {
    # R plotting characters
    '20': '.',
    '19': 'o',
    '17': '^',
    '1': 'H',
    '18': 'd',
    '15': 's',
    'small circle': 'o', # changed from .
    'circle': 'o',
    'square': 's',
    'triangle': '^',
    'rhombus': 'd',
    'ring': 'h',
    # plotly marker strings
    'circle-open': 'o', # H?
    'triangle-up': '^',
    'diamond': 'd',
    'hexagon': 'h',
    'asterisk-open': '*', # .?
}

# approximated from plotly marker size to matplotlib marker size
PCH_TO_MATPLOTLIB_MARKER_SIZE = {'.': 14, 'o': 36, 's': 20, '^': 36, 'd': 20, 'H': 28}

SERIES_TYPE_TO_PLOT_MODE = {'b': 'lines+markers', 'p': 'markers', 'l': 'lines'}

XAXIS_ORIENTATION = {0: 0, 1: 0, 2: 270, 3: 270}
YAXIS_ORIENTATION = {0: -90, 1: 0, 2: 0, 3: -90}

# Caption weights supported in Matplotlib are normal, italic and oblique.
# Map these onto the MetViewer requested values of 1 (normal), 2 (bold),
# 3 (italic), 4 (bold italic), and 5 (symbol) using a dictionary
MV_TO_MPL_CAPTION_STYLE = {
    1: ('normal', 'normal'),
    2: ('normal','bold'),
    3: ('italic', 'normal'),
    4: ('italic', 'bold'),
    5: ('oblique','normal'),
}

# Matplotlib constants
MPL_FONT_SIZE_DEFAULT = 11

MPL_DEFAULT_BAR_WIDTH = 0.8
MPL_DEFAULT_BOX_WIDTH = 0.5
