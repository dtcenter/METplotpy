
**Scatter plot README**

This file describes the informaton pertaining to generating scatter plots in Python Plotly.  The user must supply
a custom configuration file indicating the text files that correspond to each scatter.  One file per scatter, where
each file is a list of x- and y-point values.

If the data contains missing values, these **must** be replaced with the text **None**.

Each scatter must have an accompanying setting in the custom configuration file.

The default config file has dummy data for two scatters and provides an example of a simple scatter plot with both scatters
possessing the same text color, width, and scatter style.

** How to Run **

Set your *PYTHONPATH* to path-where-source-is-located/METplotpy/metplotpy and

*METPLOTPY_BASE* to path-where-source-is-located/METPlotpy

There are two sample data files and a sample custom config file already available in the directory
where the scatter.py script resides.

Then from the command scatter, run python scatter.py

In your default browser, you will see a sample scatter plot containing two scatters.

**Required configuration values:**

*title*: Title of the plot

*connect_data_gaps*: if there are missing values (None), then if set to True, connect only contiguous points, if
False, connect all available points, regardless if there is missing data between points.

*xaxis_title*: The title for the x-axis

*yaxis_title*: The title for the y-axis

*scatters*:  a list of scatters (traces) that will comprise this scatter plot.  Each scatter/trace consists of a name, data_file,
width, and dash setting.  Repeat for each subsequent scatter/trace.  Begin each scatter/trace with a *-name* and then align
the data_file, color, width, and dash indentation to match that of the *-name*.

*-name*: The title/name for the first scatter/trace on the plot.

*data_file*: full path to the input data file for the first scatter/trace to be plotted

*color*: The specific name of the color (eg. brickred, green, black, etc)

*width*: The width of the scatter in pixels.  Any integer value greater than or equal to 0, larger value results in thicker scatter.

*dash*: Style of the connecting scatter, if left blank/un-specified, then solid scatter.  Other options are dash and dot.

*-name*: The nth scatter corresponding to the nth data file.

*data_file*: The full path to the nth data file corresponding to the nth scatter/trace to be plotted

*color*: The specific name of the color to be applied to the scatter (e.g. brickred, black, blue, red)

*width*: The width of the scatter, in pixels.  An integer value greater or equal to 0,
 wlarger numbers indicate a thicker scatter.

*dash*: The style of the scatter connecting the data points, if left empty or is unspecified, a solid
    scatter will be drawn.  Other options: dash, dot
