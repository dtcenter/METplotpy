*******************
Reliability Diagram
*******************

Description
===========
Reliability diagrams are useful in displaying the conditional bias of
probabilistic forecasts.
For more information about reliability diagrams, refer to the
`METviewer documentation <https://metviewer.readthedocs.io/en/latest/Users_Guide/reliabilityplots.html>`_.

Example
=======

Sample Data
___________

The data is text output from MET in columnar format.
The sample data used to create an example reliability diagram is available
in the METplotpy repository, where the reliability diagram code is located:

*$METPLOTPY_BASE/metplotpy/test/reliability_diagram/plot_20210311_145053.data*

*$METPLOTPY_BASE* is the directory where the METplotpy code is saved:

e.g.

*/usr/path/to/METplotpy*  if the source code was cloned or forked from the Github repository

or

*/usr/path/to/METplotpy-x.y.z*  if the source code was downloaded as a zip or gzip'd tar file from the Release link of
the Github repository.  The *x.y.z* is the release number.



Configuration Files
___________________

The reliability diagram utilizes YAML configuration files to indicate where
input data is located and to set plot attributes. These plot attributes
correspond to values that can be set via the METviewer tool. YAML is a
recursive acronym for "YAML Ain't Markup Language" and according to
`yaml.org <https://yaml.org>`_, it is a "human-friendly data serialization
language". It is commonly used for configuration files and in applications
where data is being stored or transmitted.   Two configuration files are
required. The first is a default configuration file,
**reliability_defaults.yaml**, which is found in the
*$METPLOTPY_BASE/metplotpy/plots/config* directory. All default
configuration files are located in the
*$METPLOTPY_BASE/metplotpy/plots/config* directory.
**Note**: *$METPLOTPY_BASE* is the user-specified directory where the
METplotpy source code has been saved.  **Default configuration files
are automatically loaded by the plotting code and do not need to
be explicitly specified when generating a plot**

The second required configuration file is a user-supplied “custom”
configuration file. This  file is used to customize/override the default
settings in the **reliability_defaults.yaml** file. The custom configuration
file can be an empty file if all default settings are to be applied.

METplotpy Configuration
=======================

Default Configuration File
__________________________

The following is the *mandatory*, **reliability_defaults.yaml** configuration
file, which serves as a starting point for creating a reliability diagram
plot as it represents the default values set in METviewer.

**NOTE**: This default configuration file is automatically loaded by
**reliability_diagram.py**.

.. literalinclude:: ../../metplotpy/plots/config/reliability_defaults.yaml


In the default config file, logging is set to stdout and the log level is INFO (i.e. any log messages
of type INFO, WARNING, and ERROR will be logged).  If the log_filename and log_level are
not specified in the custom configuration file, these settings will be used


Custom Configuration File
_________________________

A second, *mandatory* configuration file is required, which is
used to customize the settings to the reliability diagram plot.
The **custom_reliability.yaml**
file is included with the source code an looks like the following:

.. literalinclude:: ../../test/reliability_diagram/custom_reliability_diagram.yaml

Copy this custom config file from the directory where the source code
was saved to the working directory:

.. code-block:: ini

  cp $METPLOTPY_BASE/test/reliability_diagram/custom_reliability_diagram.yaml $WORKING_DIR/custom_reliability_diagram.yaml

Modify the *stat_input* setting in the
*$METPLOTPY_BASE/test/reliability_diagram/custom_reliability_diagram.yaml*
file to explicitly point to the
*$METPLOTPY_BASE/test/reliability_diagram/reliability_diagram*
directory (where the custom config files and sample data reside).
Replace the relative path *./plot_20210311_145053.data*
with the full path
*$WORKING_DIR/METplotpy/test/reliability_diagram/plot_20210311_145053.data*
(including replacing *$METPLOTPY_BASE* with the full path to the METplotpy
installation on the system).
Modify the *plot_filename* setting to point to the output path where the
plot will be saved, including the name of the plot.

For example:

*stat_input: /username/myworkspace/METplotpy/test/reliability_diagram/plot_20210311_145053.data*

*plot_filename: /username/working_dir/output_plots/reliability_diagram_custom.png*

This is where */username/myworkspace/METplotpy* is *$METPLOTPY_BASE* and
*/username/working_dir* is *$WORKING_DIR*.  Make sure that the
*$WORKING_DIR* directory that is specified exists and has the appropriate
read and write permissions.  The path listed for *plot_filename* may
be changed to the output directory of one's choosing.  If this is not set,
then the *plot_filename* setting specified in the
*$METPLOTPY_BASE/metplotpy/plots/config/reliability_diagram_defaults.yaml*
configuration file will be used.

To save the intermediate **.points1** file (used by METviewer and useful
for debugging), set the *dump_points_1* setting to True.
Uncomment or add (if it doesn't exist) the *points_path* setting:

*dump_points_1: 'True'*

*points_path: '/dir_to_save_points1_file'*

Replace the */dir_to_save_points1_file* to the directory where
the **.points1** file is saved. If points_path
is commented out (indicated by a '#' symbol in front of it),
remove the '#' symbol to uncomment the points_path so that it will be
used by the code.  Make sure that this directory exists and has the
appropriate read and write permissions.  **NOTE**: The *points_path* setting
is **optional** and does not need to be defined in the configuration
file unless saving the intermediate **.points1** file is desired.

To save the log output to a file, uncomment the *log_filename* entry and specify the path and
name of the log file.  Select a directory with the appropriate read and write
privileges.  To modify the verbosity of logging than what is set in the default config
file, uncomment the *log_level* entry and specify the log level  (debug and info are higher verbosity, warning and error
are lower verbosity).


Using Defaults
______________

If the user wishes to use all the default settings defined in the
**reliability_defaults.yaml** file, an empty custom configuration file
(**custom_reliability_use_defaults.yaml**) can be specified (as long
as the user has write permissions for the output filename path
corresponding to the *plot_filename* setting in the default
configuration file. Otherwise, this will need to be specified in
*plot_filename* in the **minimal_box.yaml** file):

.. literalinclude:: ../../test/reliability_diagram/custom_reliability_use_defaults.yaml

Copy this file to the working directory:

.. code-block:: ini

  cp $METPLOTPY_BASE/test/reliability_diagram/minimal_reliability_diagram.yaml $WORKING_DIR/minimal_reliability_diagram.yaml

Add the *stat_input* (input data) and *plot_filename* (output file/plot)
settings to the *$WORKING_DIR/minimal_reliability_diagram.yaml*
file (anywhere below the comment block). The *stat_input* setting
explicitly indicates where the sample data and custom configuration
files are located.

Set the *stat_input* to
*$METPLOTPY_BASE/test/reliability_diagram/plot_20210311_145053.data*
and set the *plot_filename* to
*$WORKING_DIR/output_plots/reliability_diagram_default.png*:

*stat_input: $METPLOTPY_BASE/test/reliability_diagram/plot_20210311_145053.data*

*plot_filename: $WORKING_DIR/output_plots/reliability_diagram_default.png*

*$WORKING_DIR* is the working directory where all the custom
configuration files are saved. **NOTE**: To specify the *plot_filename*
(output directory) to a directory other than the
*$WORKING_DIR/output_plots*, this can be done as long as it is an
existing directory where the user has read and write permissions.

To save the intermediate **.points1** file (used by METviewer and useful
for debugging), add the following lines to the
**minimal_reliability_diagram.yaml** file (anywhere below the comment block):

*dump_points_1: 'True'*

*points_path: '/dir_to_save_points1_file'*

Replace the */dir_to_save_points1_file* to the same directory where the
**.points1** file is located.
Make sure that this directory exists and has the appropriate read and
write permissions. **NOTE**: the *points_path* setting
is **optional** and does not need to be defined in the configuration
file unless saving it to the intermediate **.points1** file is desired.

Run from the Command Line
=========================

The reliability diagram plot that uses only the default values defined in
the **reliability_defaults.yaml** configuration file looks like the following:

.. image:: figure/default_reliability_diagram.png

To generate the above plot, use the **reliability_defaults.yaml** file,
the "empty" custom configuration file and the
**custom_reliability_use_defaults.yaml** config file.

Perform the following:

* Clone the code from the `METplotpy repository
  <https://github.com/dtcenter/METplotpy>`_ (To see the page, login to Github):

  .. code-block:: ini

    cd $METPLOTPY_BASE
    git clone https://github.com/dtcenter/METplotpy

* If using the conda environment, verify the conda environment is
  running and has has the required Python packages outlined in
  the `requirements section
  <https://metplotpy.readthedocs.io/en/latest/Users_Guide/installation.html#python-requirements>`_.

* Set the METPLOTPY_BASE environment variable to point to
  *$METPLOTPY_BASE*.

  For the ksh environment:

  .. code-block:: ini

    export METPLOTPY_BASE=$METPLOTPY_BASE

  For the csh environment:

  .. code-block:: ini

    setenv METPLOTPY_BASE $METPLOTPY_BASE

  Replacing the *$METPLOTPY_BASE* with the directory where the
  METplotpy source code was saved.

* Enter the following command:

  .. code-block:: ini

    python $METPLOTPY_BASE/metplotpy/plots/reliability_diagram/reliability.py $WORKING_DIR/custom_reliability_use_defaults.yaml

* A **default_reliability_diagram.png** output file will be created in the
  directory specified in the *plot_filename* configuration setting
  in the **minimal_reliability.yaml** config file.
  The filename is specified by the *plot_filename* value in the
  **reliability_defaults.yaml** config file.

  To generate a **customized** reliability diagram (i.e. some or all
  default configuration settings are to be overridden), use the
  **custom_reliability_diagram.yaml** config file.

* Enter the following command:

  .. code-block:: ini
		
    python $METPLOTPY_BASE/metplotpy/plots/reliability_diagram/reliability.py $WORKING_DIR/custom_reliability_diagram.yaml

  In this example, this custom config file changes the color of the boxes.

  .. image:: figure/custom_reliability_diagram.png

* A **custom_reliability_diagram.png** output file will be created in
  the directory specified in the *plot_filename* configuration setting
  in the **custom_reliability_diagram.yaml** config file.
