********
Box plot
********

Description
===========

Box plots, or box and whisker plots, are a way to summarize a distribution
of values using Tukey's 5-number summary
(:ref:`Hoaglin et al., 1983<Hoaglin>`). The dark
line in the middle of the boxes (sometimes called the 'waist') is the
median of data. Half of the data values have a value greater than the
median, and half have a value lower. The actual box (i.e. the central
rectangle) spans the first quartile to the third quartile (or the
interquartile range or IQR). Whiskers extend to 1.5 times the height
of the box or, if closer to the median, the minimum or maximum values
of the data. The points represent outliers: any data point more than
1.5 times the IQR away from the median. These are defined as values
that do not fall inside the whiskers. Outliers are extreme values.
It is used by METviewer for generating box plots.
Refer to the 
`METviewer documentation
<https://metviewer.readthedocs.io/en/latest/Users_Guide/boxplot.html>`_
for details on how this plot is utilized.




Example
=======

Sample Data
___________

The sample data used to create an example box plot is available in the
METplotpy repository, where the box plot tests are located:

*$METPLOTPY_SOURCE/METplotpy/metplotpy/test/box/box.data*

*$METPLOTPY_SOURCE* is the directory where the METplotpy code is saved
(e.g. */username/myworkspace*).  The data is text output from MET in
columnar format.

Configuration Files
___________________

The box plot utilizes YAML configuration files to indicate where input data
is located and to set plot attributes. These plot attributes correspond
to values that can be set via the METviewer tool. YAML is a recursive acronym
for "YAML Ain't Markup Language" and according to
`yaml.org <https://yaml.org>`_,
it is a "human-friendly data serialization language". It is commonly used for
configuration files and in applications where data is being stored or
transmitted. Two configuration files are required. The first is a default
configuration file, **box_defaults.yaml**, which is found in the
*$METPLOTPY_SOURCE/METplotpy/metplotpy/plots/config* directory. All default
configuration files are located in the
*$METPLOTPY_SOURCE/METplotpy/metplotpy/plots/config* directory.
*$METPLOTPY_SOURCE* is the user-specified directory where the
METplotpy source code has been saved. **Default configuration files
are automatically loaded by the plotting code and do not need to be
explicitly specified when generating a plot**.

The second required configuration file is a user-supplied “custom”
configuration file. This  file is used to customize/override the default
settings in the **box_defaults.yaml** file. The custom configuration
file can be an empty file if all default settings are to be applied.

METplus Configuration
=====================

Default Configuration File
__________________________

The following is the *mandatory*, **box_defaults.yaml** configuration file,
which serves as a good starting point for creating a line
plot as it represents the default values set in METviewer.

.. literalinclude:: ../../metplotpy/plots/config/box_defaults.yaml

Custom Configuration File
_________________________

A second, *mandatory* configuration file is required, which is
used to customize the settings to the box plot. The **custom_box.yaml**
file is included with the source code.  If the user
wishes to use all the default settings defined in the **box_defaults.yaml**
file, an empty custom configuration file can be specified instead.

.. literalinclude:: ../../test/box/custom_box.yaml

Copy this custom config file from the directory where the source code was
saved to the working directory:

.. code-block:: ini
		
  cp $METPLOTPY_SOURCE/METplotpy/test/box/custom_box.yaml $WORKING_DIR/custom_box.yaml

Modify the *stat_input* setting in the
*$METPLOTPY_SOURCE/METplotpy/test/box/custom_box.yaml*
file to explicitly point to the *$METPLOTPY_SOURCE/METplotpy/test/box*
directory (where the custom config files and sample data reside).
Replace the relative path *./box.data*
with the full path *$METPLOTPY_SOURCE/METplotpy/test/box/box.data*.
Modify the *plot_filename* setting to point to the output path where the
plot will be saved, including the name of the plot.

For example:

*stat_input: /username/myworkspace/METplotpy/test/box/box.data*

*plot_filename: /username/working_dir/output_plots/box.png*

This is where */username/myworkspace/* is *$METPLOTPY_SOURCE* and
*/username/working_dir* is *$WORKING_DIR*.  Make sure that the
*$WORKING_DIR* directory that is specified exists and has the appropriate
read and write permissions.

The path listed for *plot_filename* may be
changed to the output directory of one's  choosing.  If this is not set,
then the *plot_filename* setting specified in the
*$METPLOTPY_SOURCE/METplotpy/metplotpy/plots/config/box_defaults.yaml*
configuration file will be used.

To save the intermediate **.points1** file (used by METviewer and useful
for debugging but not required), set the *dump_points_1*
setting to True. Uncomment or add (if it doesn't exist) the
*points_path* setting.

*dump_points_1: 'True'*

*points_path: '/dir_to_save_points1_file'*


Replace the **/dir_to_save_points1_file** to the same directory where
the **.points1** file is saved.
If *points_path* is commented out (indicated by a '#' symbol in front of it),
remove the '#' symbol to uncomment the points_path so that it will be used
by the code.  Make sure that this directory exists and has the
appropriate read and write permissions.  **NOTE**: the *points_path* setting
is **optional** and does not need to be defined in the configuration file
unless saving the intermediate **.points1** file is desired.


Using Defaults
______________

To use the *default* settings defined in the **box_defaults.yaml**
file, specify a minimal custom configuration file (**minimal_box.yaml**),
which consists of only a comment block, but can be any empty file (if
the user has write permissions for the output filename path corresponding to
the *plot_filename* setting in the default configuration file. Otherwise
the user will need to specify a *plot_filename* in the  **minimal_box.yaml**
file):

.. literalinclude:: ../../test/box/minimal_box.yaml

Copy this file to the working directory:

.. code-block:: ini

  cp $METPLOTPY_SOURCE/METplotpy/test/box/minimal_box.yaml $WORKING_DIR/minimal_box.yaml

Add the *stat_input* (input data) and *plot_filename* (output file/plot path)
settings to the **$WORKING_DIR/minimal_box.yaml**
file (anywhere below the comment block). The *stat_input* setting
explicitly indicates where the sample data and custom configuration
files are located.  Set the *stat_input* to
*$METPLOTPY_SOURCE/METplotpy/test/box/box.data* and set the
*plot_filename* to **$WORKING_DIR/output_plots/box_default.png**:

*stat_input: $METPLOTPY_SOURCE/METplotpy/test/box/box.data*

*plot_filename: $WORKING_DIR/output_plots/box_default.png*

Where *$WORKING_DIR* is the working directory where where all the custom
configuration files are being saved. **NOTE**: If the *plot_filename*
(output directory) is specified to a directory other than the
*$WORKING_DIR/output_plots*, the user must have read and write permissions
to that directory.

**NOTE**: This file does not plot any data, its purpose is to provide a
template for setting the margins, plot size, labels, etc.

Run from the Command Line
=========================

Perform the following to generate the plots:

* Set the METPLOTPY_BASE environment variable to point to
  *$METPLOTPY_SOURCE/METplotpy/metplotpy*.

  For the ksh environment:

  .. code-block:: ini

    export METPLOTPY_BASE=$METPLOTPY_SOURCE/METplotpy/metplotpy

  For the csh environment:

  .. code-block:: ini

    setenv METPLOTPY_BASE $METPLOTPY_SOURCE/METplotpy/metplotpy

  Replacing the *$METPLOTPY_SOURCE* with the directory where the
  METplotpy source code was saved.

  The **custom_box.yaml** configuration file, in combination with the
  **box_defaults.yaml** configuration file, generates a customized
  box plot:

  .. image:: box.png

  To generate the above plot using the **box_defaults.yaml** and
  **custom_box.yaml** config files, perform the following:

* If the conda environment is being used, verify the conda environment
  is running and has the required
  `Python packages
  <https://metplotpy.readthedocs.io/en/latest/Users_Guide/installation.html#python-requirements>`_
  outlined in the requirements section.

  The **minimal_box.yaml** configuration file, in combination with the
  **box_defaults.yaml** configuration file, generates a "default" box plot.
  **The purpose of this is to provide a
  template/starting point for setting up the margins, plot size, labels, etc.
  and does not plot any data**:

  .. image:: box_default.png

  To generate the above *"defaults"* plot (i.e using default configuration
  settings), use the "minimal" custom configuration file, **minimal_box.yaml**.


* Enter the following command.

  .. code-block:: ini
       
   python $METPLOTPY_SOURCE/METplotpy/metplotpy/plots/box/box.py $WORKING_DIR/minimal_box.yaml

* A **box_default.png** output file will be created in the
  directory specified in the *plot_filename* configuration setting in
  the **box_minimal.yaml** config file.
