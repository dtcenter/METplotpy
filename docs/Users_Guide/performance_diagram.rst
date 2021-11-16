*******************
Performance Diagram
*******************

Description
===========

Performance diagrams are used to show the relationship between categorical
statistics, with  axes representing detection and success (1 - false alarm)
rates (:ref:`Roebber, 2009<Roebber>`).  
The simplest input to the performance diagram is the MET contingency
table statistics (CTS)  output.  This output can be produced by many of
the MET tools (Point-Stat, Grid-Stat, etc.). 


There are several reference lines on the performance diagram.  The dashed
lines that radiate from the origin are lines of equal frequency bias.
Labels for the frequency bias amount are at the end of each line. The
diagonal represents a perfect frequency bias score of 1.  Curves of
equal Critical Success Index (CSI) connect the top of the plot to the
right side.  CSI amounts are listed to the right side of the plot,
with better values falling closer to the top.

Example
=======

Sample Data
___________

The sample data used to create these plots is available in the METplotpy
repository, where the performance diagram scripts are located:

*$METPLOTPY_SOURCE/METplotpy/metplotpy/plots/plot_20200317_151252.data*

*$METPLOTPY_SOURCE* is the directory where the METplotpy code is saved.
The data is text output from MET in columnar format.



Configuration Files
___________________

The performance diagram utilizes YAML configuration files to indicate where
input data is located and to set plot attributes. These plot attributes
correspond to values that can be set via the METviewer tool. YAML is a
recursive acronym for "YAML Ain't Markup Language" and according to
`yaml.org <https://yaml.org>`_,
it is a "human-friendly data serialization language. It is commonly used for
configuration files and in applications where data is being stored or
transmitted. Two configuration files are required. The first is a
default configuration file, **performance_diagram_defaults.yaml**,
which is found in the
*$METPLOTPY_SOURCE/METplotpy/metplotpy/plots/config* directory. All default
configuration files are located in the
*$METPLOTPY_SOURCE/METplotpy/metplotpy/plots/config* directory.
Note: *$METPLOTPY_SOURCE* is the user-specified directory where the
METplotpy source code has been saved.

The second required configuration file is a user-supplied “custom”
configuration file. This  file is used to customize/override the default
settings in the **performance_diagram_defaults.yaml** file. The custom
configuration file can be an empty file if all default settings are to
be applied.

Default Configuration File Settings
___________________________________

* **title**  The title for the performance diagram.

* **title_weight**  1=plain 2=bold 3=italic 4=bold italic.

* **title_align**  Unsupported by Matplotlib, included for consistency
  with METviewer.

* **title_offset**  Unsupported by Matplotlib, included for consistency
  with METviewer.

* **title_size**  Magnifier value. Values above 1.0 create title 
  that is larger than the internal default size. Values less than
  1.0 create a title that is smaller than the internal default size.

* **xaxis**  The label to the x-axis.

* **yaxis_1**  The label to the bottom y-axis.

* **yaxis_2**  The label to the top y-axis (leave empty if second y-axis 
  is not needed/required).

* **plot_width**  Width of plot in inches.

* **plot_height** Height of plot in inches.

* **plot_units**  Units for plot: in for inches or cm for centimeters.

* **plot_ci**  A list of values of the type of Confidence Intervals to apply.
  Choose either None for no confidence intervals or Norm for normalized
  confidence intervals.
               

* **plot_disp**  A list of True/False values. True to display, False otherwise.

* **series_order**  A list of values 1..n indicating the order of the
  series in the list.
  e.g. if the list is 3, then 1, then 2 this indicates that the first
  series in the list is to be treated as the third, the second element in
  the list is to be treated as the first series, and the third element
  in the list is to be treated as the second series.
 
* **indy_var**  The independent variable.

* **indy_vals**  A list of independent variables.

* **fcst_var_val_1**  Variables of interest.

* **fcst_var_val_2**  Second set of variables of interest.
                 
* **series_val_1**  Series values.

* **series_val_2**  Second set of series values. Leave as empty.

* **list_stat_1**  List of statistics of interest .

* **list_stat_2**  Second list of statistics of interest. Leave as empty
  list.

* **user_legend**  List of legend labels.  One for each series. If any list
  member is empty, a legend label will be created based on other information.

* **legend_box**
  'n' for no box around the legend.
  'o' for a box drawn around the legend.

* **legend_ncol**  Integer value indicating how many columns of
  legend labels.

* **legend_inset**  x and y values indicating position of the legend.

* **legend_size**  A magnification value.  Value greater than 1.
  Produces a legend that is greater than an internal default value.
  Value less than 1.0 produces a legend smaller than an internal default size.

* **plot_stat**  The statistics to plot: median, mean or sum.

* **plot_contour_legend**  True for drawing a legend for contour lines,
  False otherwise.

* **colors**  A list of colors one for each series. Define as color
  name or hexadecimal values.

* **series_line_width**  A list of widths for each series line.
  Values greater than 1 result in a thicker line.

* **series_symbols**  A list of symbols to apply for each series:
  'o' for circle, 's' for square, 'H' for ring, 'd' for diamond,
  '^' for triangle.

* **series_line_style**  A list of line styles to apply to the
  corresponding series:
  '-' for solid line
  '--' for dashed line
  ':' for dotted line.

* **event_equal**  True to perform event equalization on data, False otherwise.

* **annotation_template**  Annotation for y-value.  Leave empty if
  no annotation is desired.
  Otherwise, indicate template with "%y <units>".  Double quotes around
  annotation are needed.

* **plot_caption**  Caption text, leave empty if no caption is desired.

* **caption_weight**  1=plain text 2=bold 3=italic 4=bold italic.

* **caption_col**  Color of caption, color name or hexadecimal value.

* **caption_size**  Relative magnification of an internal default font size.

* **caption_offset**  The up/down position relative to the x-axis.

* **caption_align**  The left/right position relative to the y-axis.

* **xlab_size**  Size of the x label as a magnification of an internal
  default size.

* **xlab_align**  The up/down positioning relative to x-axis.

* **xlab_offset**  The left/right position relative to the y-axis.

* **xlab_weight**  1=plain text 2=bold 3=italic 4=bold italic.

* **xtlab_orient**  Unsupported by Matplotlib, kept for consistency
  with METviewer.

* **xtlab_size**  Unsupported by Matplotlib, kept for consistency
  with METviewer.

* **ylab_align**  The left/right position of y label.

* **ylab_offset**  The up/down position of y label.

* **ylab_weight**  1=plain text, 2=bold, 3=italic, 4=bold italic.

* **ytlab_orient**  The y-tick label orientation.

* **ytlab_size**  Size of y-tick labels as a magnification of an
  internal default size.

* **stat_input**  Path and filename of the input MET stat file.

* **plot_filename**  Path and filename of the output performance diagram
  PNG file.  Only PNG output is currently supported.

Run from the Command Line
=========================

To generate a default performance diagram (i.e. using settings in the 
**performance_diagram_defaults.yaml** configuration file), clone the code
from the `METplotpy repository at GitHub
<https://github.com/dtcenter/METplotpy>`_.
From the command line:

.. code-block:: ini
		
   cd $METPLOTPY_SOURCE
   git clone https://github.com/dtcenter/METplotpy

Change directory to
*$METPLOTPY_SOURCE/METplotpy/metplotpy/plots/performance_diagram*, where
*$METPLOTPY_SOURCE* is the directory where the code was cloned.  

.. code-block:: ini
		
   cd $METPLOTPY_SOURCE/METplotpy/metplotpy/plots/performance_diagram


Activate the conda environment, which has all the Python requirements
outlined in the :ref:`Installation guide<python_req>`.

Run the following on the command line:

.. code-block:: ini

  python performance_diagram.py ./minimal_performance_diagram.yaml

This will create a PNG file, **performance_diagram_default.png**, in the
same directory where the python command ran.


To generate a slightly modified plot, re-run the above command using the
custom_performance_diagram.yaml file:

.. code-block:: ini
		
  python performance_diagram.py ./custom_performance_diagram.yaml

This will create a PNG file, **performance_diagram_custom.png**, which
will differ in appearance from the default plot.  These plots use the
**plot_20200317_151252.data** that is found in the
*METplotpy/metplotpy/plots/performance_diagram* directory, and creates the
PNG plot in addition to a **plot_2020-317_151252.points1** file.  The
latter is a text file that contains the x- and y-values that are being
plotted and is useful in debugging.  
