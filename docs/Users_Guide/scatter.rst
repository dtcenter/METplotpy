************
Scatter Plot
************

Description
===========
The scatter plot is useful for illustrating relationships between pairs of continuous variables.
This plot was developed to support plotting MPR (matched pair) data from the MET point-stat tool.
**NOTE** This MET output data must first be reformatted into a format that can be read in by the scatter plot code.
This reformatting was accomplished through the METdataio METreformat module. The reformatted data
consists solely of MPR linetype data and all the column headers are labelled according to the
MPR linetype column names specified in the MET User's Guide, Table 11.20 (Point-stat tool).
In addition to selecting the two continuous variables to plot, the points in the scatter plot are colored based on
their value.  These colors are determined by specifying a colormap in the user configuration file.

Example
=======

Sample Data
-----------

The data is text output from the MET point-stat tool. The data is arranged in columnar format and reformatted by the
METdataio METreformat module.

The sample data for creating the example scatter plot is available in the
`METplotpy <https://github.com/dtcenter/METplotpy>`_ repository, where the scatter plot tests are located:

    *$METPLOTPY_BASE/metplotpy/test/scatter/reformatted_data_for_scatter.data*

*$METPLOTPY_BASE* is the directory where the METplotpy code is saved:

e.g.

*/usr/path/to/METplotpy* if the source code was cloned or forked from the Github repository

or

*/usr/path/to/METplotpy-x.y.z* if the source code was downloaded as a zip or gzip'd tar file from the Release link of
the Github repository.  The *x.y.z* is the release number.

**NOTE**:
The MPR linetype data produced by the MET point-stat tool has been reformatted via the METdataio METreformat
module.

Configuration Files
-------------------

The scatter plot utilizes YAML configuration files to indicate where input
data is located and to set plot attributes. YAML is a recursive
acronym for "YAML Ain't Markup Language" and according to
`yaml.org <https://yaml.org>`_, it is a
"human-friendly data serialization language".
It is commonly used for configuration files and in applications where
data is being stored or
transmitted. Two configuration files are required. The first is a default
configuration file, **scatter_defaults.yaml**, which is found in the
*$METPLOTPY_BASE/metplotpy/plots/config* directory. All default
configuration files are located in the
*$METPLOTPY_BASE/metplotpy/plots/config* directory.
*$METPLOTPY_BASE* is base directory where the
METplotpy source code has been saved. **Default configuration files are
automatically loaded by the plotting code and do not need to be explicitly
specified when generating a plot**. In addition, the default configuration file
**DOES NOT require any modifications**.

The second required configuration file is a user-supplied “custom”
configuration file. This file is used to customize/over ride the default
settings in the **scatter_defaults.yaml** file. The custom configuration
file can contain only those settings that will over ride the default settings in the
scatter_defaults.yaml config file.

.. note::

  The YAML configuration files do not support expanding environment variables. If you see an environment variable
  referenced in this documentation for a YAML configuration item, please be aware the full value of that environment
  variable must be used.

METplus Configuration
=====================

Default Configuration File
--------------------------

The following is the *mandatory*, **scatter_defaults.yaml** configuration file,
which serves as a good starting point for creating a scatter
plot as it represents the default values set in METviewer.  This default config file
is **NOT** to be configured.  Use the custom configuration file to over ride the settings
of interest (i.e. marker colors, marker styles, trendline styles, etc.).

**NOTE**: This default configuration file is automatically loaded by
**scatter.py**.

.. literalinclude:: ../../metplotpy/plots/config/scatter_defaults.yaml

In the default config file, logging is set to *stdout* and the log level is *ERROR* (i.e. any log messages
of type ERROR will be logged).  If the log_filename and log_level are
not specified in the custom configuration file, these settings will be used.

To save the log to a file and
change the log level, set the log_filename and log_level to the desired values in the custom config file.
*DO NOT* modify the default configuration file.


Custom Configuration File
-------------------------

A second, *mandatory* configuration file is required, which is
used to customize the settings to the scatter plot. The **test_scatter_mpr.yaml**
file is included with the source code.

.. literalinclude:: ../../test/scatter/test_scatter_mpr.yaml

Copy this custom config file from the directory where the source code was
saved to the working directory:

.. code-block:: ini
		
  cp $METPLOTPY_BASE/test/scatter/test_scatter_mpr.yaml $WORKING_DIR/custom_scatter.yaml


Modify the *stat_input* setting in the
*$METPLOTPY_BASE/test/scatter/custom_scatter.yaml* file to
explicitly point to the *$METPLOTPY_BASE/test/scatter*
directory (where the custom config files and sample data reside).
Replace the relative path *./scatter.data* with the full path
*$METPLOTPY_BASE/test/scatter/scatter.data*
(including replacing *$METPLOTPY_BASE* with the full path to the METplotpy
installation on the system).

Modify the *plot_filename*
setting to point to the output path where the plot will be saved,
including the name of the plot.


For example:

*stat_input: /username/myworkspace/METplotpy/test/scatter/reformatted_data_for_scatter.data*

*plot_filename: /username/working_dir/output_plots/scatter.png*

This is where */username/myworkspace/METplotpy* corresponds to *$METPLOTPY_BASE* and
*/username/working_dir* corresponds to *$WORKING_DIR*.  Make sure that the
*$WORKING_DIR* directory that is specified exists and has the appropriate
read and write permissions.  The path listed for *plot_filename* may be
changed to the output directory of one's choosing.  If this is not set,
then the *plot_filename* setting specified in the
*$METPLOTPY_BASE/metplotpy/plots/config/scatter_defaults.yaml*
configuration file will be used.

To save the intermediate **plot_points.txt** file, set the *dump_points*
setting to True.

Modify the *points_path* setting or add it (if it doesn't exist).

*dump_points: 'True'*

*points_path: '/dir_to_save_plot_points_file'*

Replace the */dir_to_save_plot_points_file* to the same directory where
the ***plot_points.txt** file is saved.
Make sure that this directory has the appropriate read and write permissions.

To save the log output to a file, uncomment the *log_filename* entry and specify the path and
name of the log file.  Select a directory with the appropriate read and write
privileges.

To modify the verbosity of logging than what is set in the default config
file, uncomment the *log_level* entry and specify the log level  (debug and info are higher verbosity, warning and error
are lower verbosity).



Run from the Command Line
=========================

The **custom_scatter.yaml** configuration file, in combination with the
**scatter_defaults.yaml** configuration file, generates a plot of the matched
pair (MPR) linetype data for the TMP variable and the two continuous variables FCST and OBS.
The grid lines and trendline are turned on, the FCST, OBS, and OBS_LAT points are saved to a text file, and the
OBS_LAT points are colored by their values using a colormap:

.. image:: figure/scatter.png

To generate the above plot using the **scatter_defaults.yaml** and
**custom_scatter.yaml** config files, perform the following:

* If using the conda environment, verify the conda environment
  is running and has the required
  `Python packages
  <https://metplotpy.readthedocs.io/en/latest/Users_Guide/installation.html#python-requirements>`_
  outscatterd in the requirements section.

* Set the METPLOTPY_BASE environment variable to point to
  *$METPLOTPY_BASE*.

  For the ksh environment:

  .. code-block:: ini
		
    export METPLOTPY_BASE=$METPLOTPY_BASE

  For the csh environment:

  .. code-block:: ini

    setenv METPLOTPY_BASE $METPLOTPY_BASE

  Recall that *$METPLOTPY_BASE* is the directory path indicating where the METplotpy source code was saved.

  To generate the above **"custom"** plot (i.e using some custom
  configuration settings), use the custom configuration file,
  **custom_scatter.yaml** that was edited with the appropriate paths to the input and output directories and files.

* Enter the following command:
  
  .. code-block:: ini

    python $METPLOTPY_BASE/metplotpy/plots/scatter/scatter.py $WORKING_DIR/custom_scatter.yaml


* A **scatter_mpr_tmp_obs_lat.png** output file will be created in the directory specified in
  the *plot_filename* configuration setting in the **scatter.yaml** config file.


  .. image:: figure/scatter_mpr_tmp_obs_lat.png

