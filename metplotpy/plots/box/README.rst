
**Box plot README**

This file describes the informaton pertaining to generating box plots in Python Plotly.  The user must supply
a custom configuration file indicating the text files that correspond to each box.  One file per box, where
each file is a list of x- and y-point values.

If the data contains missing values, these **must** be replaced with the text **None**.

Each box must have an accompanying setting in the custom configuration file.

The default config file has dummy data for two boxs and provides an example of a simple box plot with both boxs
possessing the same text color, width, and box style.

** How to Run **

Set your *PYTHONPATH* to path-where-source-is-located/METplotpy/metplotpy and

*METPLOTPY_BASE* to path-where-source-is-located/METPlotpy/metplotpy

There are two sample data files and a sample custom config file already available in the directory
where the box.py script resides.

Then from the command box, run python box.py

In your default browser, you will see a sample box plot containing two boxs.

**Required configuration values:**

*title*: Title of the plot

*xaxis_title*: The title for the x-axis

*yaxis_title*: The title for the y-axis

*boxes*:  a list of boxes that will comprise this box plot.  Each box/trace consists of a name, data_file,
width, and dash setting.  Repeat for each subsequent box/trace.  Begin each box/trace with a *-name* and then align
the data_file, color, width, and dash indentation to match that of the *-name*.

*-name*: The title/name for the first box on the plot.

*data_file*: full path to the input data file for the first box to be plotted

*color*: The specific name of the color (eg. brickred, green, black, etc)

*width*: The width of the box in pixels.  Any integer value greater than or equal to 0, larger value results in thicker box.

*-name*: The nth box corresponding to the nth data file.

*data_file*: The full path to the nth data file corresponding to the nth box/trace to be plotted

*color*: The specific name of the color to be applied to the box (e.g. brickred, black, blue, red)
