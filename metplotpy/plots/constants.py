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
DEFAULT_CAPTION_Y_OFFSET = -3.1
DEFAULT_TITLE_FONT_SIZE = 11
DEFAULT_TITLE_OFFSET = (-0.48)


AVAILABLE_MARKERS_LIST = ["o", "^", "s", "d", "H", ".", "h"]
AVAILABLE_PLOTLY_MARKERS_LIST = ["circle-open", "circle",
                                 "square", "diamond",
                                 "hexagon", "triangle-up", "asterisk-open"]

PCH_TO_MATPLOTLIB_MARKER = {'20': '.', '19': 'o', '17': '^', '1': 'H',
                            '18': 'd', '15': 's', 'small circle': '.',
                            'circle': 'o', 'square': 's',
                            'triangle': '^', 'rhombus': 'd', 'ring': 'h'}

PCH_TO_PLOTLY_MARKER = {'0': 'circle-open', '19': 'circle', '20': 'circle',
                        '17': 'triangle-up', '15': 'square', '18': 'diamond',
                        '1': 'hexagon2', 'small circle': 'circle-open',
                        'circle': 'circle', 'square': 'square', 'triangle': 'triangle-up',
                        'rhombus': 'diamond', 'ring': 'hexagon2', '.': 'circle',
                        'o': 'circle', '^': 'triangle-up', 'd': 'diamond', 'H': 'circle-open',
                        'h': 'hexagon2', 's': 'square'}

PCH_TO_PLOTLY_MARKER_SIZE = {'.': 5, 'o': 8, 's': 6, '^': 8, 'd': 6, 'H': 7}

TYPE_TO_PLOTLY_MODE = {'b': 'lines+markers', 'p': 'markers', 'l': 'lines'}
LINE_STYLE_TO_PLOTLY_DASH = {'-': None, '--': 'dash', ':': 'dot', '-:': 'dashdot'}
XAXIS_ORIENTATION = {0: 0, 1: 0, 2: 270, 3: 270}
YAXIS_ORIENTATION = {0: -90, 1: 0, 2: 0, 3: -90}

PLOTLY_PAPER_BGCOOR = "white"
PLOTLY_AXIS_LINE_COLOR = "#c2c2c2"
PLOTLY_AXIS_LINE_WIDTH = 2

# Caption weights supported in Matplotlib are normal, italic and oblique.
# Map these onto the MetViewer requested values of 1 (normal), 2 (bold),
# 3 (italic), 4 (bold italic), and 5 (symbol) using a dictionary
MV_TO_MPL_CAPTION_STYLE = {1:('normal', 'normal'), 2:('normal','bold'), 3:('italic', 'normal')
    , 4:('italic', 'bold'),5:('oblique','normal')}

# Matplotlib constants
MPL_FONT_SIZE_DEFAULT = 11
