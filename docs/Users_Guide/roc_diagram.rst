***********
ROC diagram
***********

Description
===========

ROC (Receiver Operating Characteristic) curves are useful in weather
forecasting.  ROC curve plots show the true positive rate (sensitivity)
versus the false positive rate (1 - specificity) for different cut-off
points of a parameter.  In addition to creating ROC diagrams directly
from the source code in the METplotpy repository, ROC diagrams can be
generated through METviewer.  For more information on ROC diagrams, please
refer to the
`METviewer documentation
<https://metviewer.readthedocs.io/en/latest/Users_Guide/rocplot.html>`_.

Example
=======

Data
----

The ROC diagram utilizes MET CTC or PCT linetype data.  The MET .stat output files must
first be reformatted into a format recognized by the ROC diagram code.  The METdataio METreformat
module provides reformatting support for these linetypes.  Please refer to the
`METdataio User's Guide <https://metdataio.readthedocs.io/en/v3.0.0-beta3/Users_Guide/reformat_stat_data.html>`_
for instructions on reformatting the MET .stat output.

Sample Data
-----------

Sample data used to create an example ROC diagram is
available in the METplotpy repository, where the ROC diagram
code is located:

*$METPLOTPY_BASE/test/roc_diagram/plot_20200507_074426.data*

*$METPLOTPY_BASE* is the directory where the METplotpy source code
is installed. (e.g. */username/myworkspace*):

e.g.

*/usr/path/to/METplotpy*  if the source code was cloned or forked from the Github repository

or

*/usr/path/to/METplotpy-x.y.z*  if the source code was downloaded as a zip or gzip'd tar file from the Release link of
the Github repository.  The *x.y.z* is the release number.


Configuration Files
-------------------

The ROC diagram utilizes YAML configuration files to indicate where input
data is located and to set plot attributes. These plot attributes correspond
to values that can be set via the METviewer tool. YAML is a recursive
acronym for "YAML Ain't Markup Language" and according to
`yaml.org <https://yaml.org>`_, it is a "human-friendly data serialization
language". It is commonly used for configuration files and in applications
where data is being stored or transmitted.   Two configuration files are
required. The first is a default configuration file, the first is a
default configuration file, **roc_diagram_defaults.yaml** that is found in the
*$METPLOTPY_BASE/metplotpy/plots/config* directory.  All default
configuration files are located in the
*$METPLOTPY_BASE/metplotpy/plots/config*
directory.  **Default configuration files are automatically loaded by
the plotting code and do not need to be explicitly specified when
generating a plot**.

The second, required YAML configuration file is a user-supplied
"custom" configuration file that is used to customize/override the default
settings in the **roc_diagram_defaults.yaml** file.  The custom
configuration file can be an empty file if default settings are to be applied.

METplus Configuration
=====================


Default Configuration File
--------------------------

The following is the *mandatory*, **roc_diagram_defaults.yaml**
configuration file, which serves as a starting point for creating
a ROC diagram plot as it represents the default values set in METviewer.

**NOTE**: This default configuration file is automatically loaded by
**roc_diagram.py**.

.. literalinclude:: ../../metplotpy/plots/config/roc_diagram_defaults.yaml

In the default config file, logging is set to stdout and the log level is ERROR (i.e. only log messages
of type ERROR will be logged).  If the log_filename and log_level are
not specified in the custom configuration file, these settings will be used.


Custom Configuration File
-------------------------

A second, *mandatory* configuration file is required, which is
used to customize the settings to the ROC diagram plot. The
**custom_roc_diagram.yaml** file is included with the source code
and looks like the following:

.. literalinclude:: ../../test/roc_diagram/custom_roc_diagram.yaml

Copy this custom config file from the directory where the source code
was saved to the working directory:

.. code-block:: ini

  cp $METPLOTPY_BASE/test/roc_diagram/custom_roc_diagram.yaml $WORKING_DIR/custom_roc_diagram.yaml


Modify the *stat_input* setting in the
*$WORKING_DIR/custom_roc_diagram.yaml*
file to explicitly point to the
*$WORKING_DIR* directory (where the
custom config files and sample data reside).  Replace the relative path
*./plot_20200507_074426.data* with the full path
*$WORKING_DIR/plot_20200507_074426.data*
(including replacing *$WORKING_DIR* with the full path to the working directory).

Modify the *plot_filename* setting to point to the output path where the
plot will be saved, including the name of the plot.

Modify the *roc_pct* and *roc_ctc* settings in the
*$WORKING_DIR/custom_roc_diagram.yaml*
file to explicitly indicate the linetype of the input data.  If using
PCT input data, then set *roc_pct* to True and *roc_ctc* to False. The data used in this
example is CTC linetype data, therefore the *roc_pct* setting is set to False and the *roc_ctc*
setting is set to True.


For example:

*stat_input: /username/myworkspace/METplotpy/test/roc_diagram/plot_20200507_074426.data*

*plot_filename: /username/working_dir/output_plots/roc_diagram_custom.png*

This is where */username/myworkspace/METplotpy* is *$METPLOTPY_BASE* and
*/username/working_dir* is *$WORKING_DIR*.  Make sure that the
*$WORKING_DIR* directory that is specified exists and has the appropriate
read and write permissions.The path listed for *plot_filename* may be
changed to the output directory of one’s choosing.  If this is not set,
then the *plot_filename* setting specified in the
*$METPLOTPY_BASE/metplotpy/plots/config/roc_diagram_defaults.yaml*
configuration file will be used.

To save the intermediate **.points1** file (used by METviewer and useful
for debugging), set the *dump_points_1* setting to True. Uncomment or
add (if it doesn't exist) the *points_path* setting.

*dump_points_1: 'True'*

*points_path: '/dir_to_save_points1_file'*

Replace the */dir_to_save_points1_file* to the directory where
the **.points1** file is saved.  If points_path is commented out (indicated
by a '#' symbol in front of it), remove the '#' symbol to uncomment
the points_path so that it will be used by the code.  Make sure that
this directory exists and has the appropriate read and write permissions.
**NOTE**: the *points_path* setting is **optional** and does not need to
be defined in the configuration file unless saving the intermediate
**.points1** file is desired.

To save the log output to a file, uncomment the *log_filename* entry and specify the path and
name of the log file.  Select a directory with the appropriate read and write
privileges.  To modify the verbosity of logging than what is set in the default config
file, uncomment the *log_level* entry and specify the log level  (debug and info are higher verbosity, warning and error
are lower verbosity).



Using Defaults
--------------

If the user wishes to use the **default** settings defined in the
**roc_diagram_defaults.yaml** file, specify a minimal custom configuration
file (**minimal_roc_diagram.yaml**), which consists of only a comment
block, but can be any empty file (as long as the user has write permissions
for the output filename path corresponding to the
*plot_filename* setting in the default configuration file. Otherwise,
this will need to be specified in *plot_filename* in the
**minimal_roc_diagram.yaml** file):

.. literalinclude:: ../../test/roc_diagram/minimal_roc_diagram.yaml

Copy this file to the working directory:

.. code-block:: ini

  cp $METPLOTPY_BASE/test/roc_diagram/minimal_roc_diagram.yaml $WORKING_DIR/minimal_roc_diagram.yaml

Add the *stat_input* (input data) and *plot_filename*
(output file/plot path) settings to the
*$WORKING_DIR/minimal_roc_diagram.yaml* file (anywhere below the
comment block). The *stat_input* setting explicitly indicates where the
sample data and custom configuration files are located.  Set the
*stat_input* to
*$WORKING_DIR/plot_20200507_074426.data*
and set the
*plot_filename* to *$WORKING_DIR/output_plots/roc_diagram_default.png*:

*stat_input: $METPLOTPY_BASE/test/roc_diagram/plot_20200507_074426.data*

*plot_filename: $WORKING_DIR/output_plots/roc_diagram_default.png*

*$WORKING_DIR* is the working directory where  all the custom
configuration files are being saved
(including replacing *$METPLOTPY_BASE* with the full path to the METplotpy
installation on the system). **NOTE**: To specify the
*plot_filename* (output directory) to a directory other than the
*$WORKING_DIR/output_plots*, this can be done as long as it is an
existing directory where the user has read and write permissions.

To save the intermediate **.points1** file (used by METviewer and
useful for debugging), add the following lines to the
**minimal_roc_diagram.yaml** file (anywhere below the comment block):

*dump_points_1: 'True'*

*points_path: '/dir_to_save_points1_file'*


Replace the */dir_to_save_points1_file* to the same directory where
the **.points1** file is saved. Make sure that this directory exists
and has the appropriate read and write permissions. **NOTE**: the
*points_path* setting is **optional** and does not need to be defined
in the configuration file unless  saving it to the intermediate
**.points1** file is desired.


Run from the Command Line
=========================

The ROC diagram plot that uses only the default values defined in
the **roc_diagram_defaults.yaml** configuration file looks like the following:

.. image:: figure/roc_diagram_default.png

Perform the following:

* To use the conda environment, verify the conda environment
  is running and has has the required
  Python packages outlined in the `Python Requirements section
  <https://metplotpy.readthedocs.io/en/latest/Users_Guide/installation.html#python-requirements>`_.>`_:


* Set the METPLOTPY_BASE environment variable to point to
  *$METPLOTPY_BASE*

  For the ksh environment:

  .. code-block:: ini

    export METPLOTPY_BASE=$METPLOTPY_BASE

  For the csh environment:

  .. code-block:: ini

    setenv METPLOTPY_BASE $METPLOTPY_BASE

  Replacing the $METPLOTPY_BASE with the directory where the
  METplotpy source code was saved.


  To generate the above **"defaults"** plot (i.e using default
  configuration settings), use the "minimal" custom configuration file,
  **minimal_roc_diagram.yaml**.

* Enter the following command:
  
  .. code-block:: ini

    python $METPLOTPY_BASE/metplotpy/plots/roc_diagram/roc_diagram.py $WORKING_DIR/minimal_roc_diagram.yaml


* A **roc_diagram_default.png** output file will be created in the
  directory specified in the *plot_filename* configuration setting
  in the **minimal_roc_diagram.yaml** config file.

  To generate a **customized** ROC diagram (i.e. some or all default
  configuration settings are to be overridden), use the
  **custom_roc_diagram.yaml** config file.


* Enter the following command:

  .. code-block:: ini
		
    python $METPLOTPY_BASE/metplotpy/plots/roc_diagram/roc_diagram.py $WORKING_DIR/custom_roc_diagram.yaml

  In this example, this custom config file changes the title and axis
  labels. The caption magnification, caption weight, and title offset
  values were modified, resulting in the drastically different plot
  shown below.  The user will need to experiment with these values
  to achieve the desired appearance.
   

  .. image:: figure/roc_diagram_custom.png

* A **custom_roc_diagram.png** output file will be created in the
  directory that was specified in the *plot_filename* configuration
  setting in the **custom_roc_diagram.yaml** config file.
