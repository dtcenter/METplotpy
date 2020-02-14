
**Line plot README**

This file describes the information pertaining to generating line plots in Python Plotly.  The user must supply
a custom configuration file indicating the text files that correspond to each line.  One file per line, where
each file is a list of x- and y-point values.

If the data contains missing values, these **must** be replaced with the text **None**.

Each line (also referred to as 'trace') must have an accompanying setting in the custom configuration file.

The default config file has dummy data for two lines and provides an example of a simple line plot with both lines
possessing the same text color, width, and line style.

** How to Run **

Set your *PYTHONPATH* to path-where-source-is-located/METplotpy/metplotpy and

*METPLOTPY_BASE* to path-where-source-is-located/METPlotpy

There are two sample data files and a sample custom config file already available in the directory
where the line.py script resides.

Then from the command line, run python line.py

In your default browser, you will see a sample line plot containing two lines.

**Required configuration values:**

*title*: Title of the plot

*connect_data_gaps*: if there are missing values (None), then if set to True, connect only contiguous points, if
False, connect all available points, regardless if there is missing data between points.

*xaxis_title*: The title for the x-axis

*yaxis_title*: The title for the y-axis

*lines*:  a list of lines (traces) that will comprise this line plot.  Each line/trace consists of a name, data_file,
width, and dash setting.  Repeat for each subsequent line/trace.  Begin each line/trace with a *-name* and then align
the data_file, color, width, and dash indentation to match that of the *-name*.

*-name*: The title/name for the first line/trace on the plot.

*data_file*: full path to the input data file for the first line/trace to be plotted

*color*: The specific name of the color (eg. brickred, green, black, etc)

*width*: The width of the line in pixels.  Any integer value greater than or equal to 0, larger value results in thicker line.

*dash*: Style of the connecting line, if left blank/un-specified, then solid line.  Other options are dash and dot.

*-name*: The nth line corresponding to the nth data file.

*data_file*: The full path to the nth data file corresponding to the nth line/trace to be plotted

*color*: The specific name of the color to be applied to the line (e.g. brickred, black, blue, red)

*width*: The width of the line, in pixels.  An integer value greater or equal to 0,
 wlarger numbers indicate a thicker line.

*dash*: The style of the line connecting the data points, if left empty or is unspecified, a solid
    line will be drawn.  Other options: dash, dot
