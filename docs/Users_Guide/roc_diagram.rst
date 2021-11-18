ROC diagram
===========

Description
~~~~~~~~~~~

ROC (Receiver Operating Characteristic) curves are useful in weather forecasting.  ROC
curve plots show the true positive rate (sensitivity) versus the
false positive rate (1 - specificity) for different cut-off points of
a parameter.  In addition to creating ROC diagrams directly from the source code in the METplotpy
repository, ROC diagrams can be generated through METviewer.  For more information on ROC diagrams, please
refer to the METviewer documentation:

https://metviewer.readthedocs.io/en/latest/Users_Guide/rocplot.html

Example
~~~~~~~

**Sample Data**

Sample data used to create an example ROC diagram is
available in the METplotpy repository, where the ROC diagram
code is located:

$METPLOTPY_SOURCE/METplotpy/test/roc_diagram/plot_20200507_074426.data

`$METPLOTPY_SOURCE` is the directory where you have installed the METplotpy source code
(e.g. /username/myworkspace).



**Configuration Files**

The ROC diagram utilizes YAML configuration files to indicate where input data is located and
to set plot attributes. These plot attributes correspond to values that can be set via the METviewer
tool. YAML is a recursive acroynym for "YAML Ain't Markup Language" and according to yaml.org,
it is a "human-readable data-serialization language". It is commonly used for configuration files
and in applications where data is being stored or transmitted".  Two configuration files are required,
the first is a default configuration file, roc_diagram_defaults.yaml that is found in the
$METPLOTPY_SOURCE/METplotpy/metplotpy/plots/config directory.  All default
configuration files are located in the $METPLOTPY_SOURCE/METplotpy/metplotpy/plots/config
directory.  **Default configuration files are automatically loaded by the plotting code and do not
need to be explicitly specified when generating a plot**. The second, required YAML configuration file is a
user-supplied "custom" configuration file that is used to customize/override the default
settings in the roc_diagram_defaults.yaml file.  The custom configuration file can be an empty
file if default settings are to be applied.  

METplus Configuration
~~~~~~~~~~~~~~~~~~~~~


**Default Configuration File**

The following is the `mandatory`, roc_diagram_defaults.yaml configuration file,
which serves as a starting point for creating a ROC diagram plot,  as it represents
the default values set in METviewer.

**NOTE**: This default configuration file is automatically loaded by roc_diagram.py.

.. literalinclude:: ../../metplotpy/plots/config/roc_diagram_defaults.yaml



Modify the `stat_input` setting (input data file) in this default config file to ensure that the data file is accessible.
Open the $METPLOTPY_SOURCE/METplotpy/metplotpy/plots/config/roc_diagram_defaults.yaml file and replace
the relative path in the stat_input entry `stat_input:  ../../../test/roc_diagram/plot_20200507_074426.data`
with the path to your $METPLOTPY_SOURCE directory.  For example, if your $METPLOTPY_SOURCE is /username/plotting,
then the `stat_input` setting will look like the following:

`stat_input:  /username/plotting/METplotpy/test/roc_diagram/plot_20200507_074426.data`


**Custom Configuration File**


A second, `mandatory` configuration file is required, which is
used to customize the settings to the ROC diagram plot. The custom_roc_diagram.yaml
file is included with the source code and looks like the following:

.. literalinclude:: ../../test/roc_diagram/custom_roc_diagram.yaml

copy this custom config file from the directory where you saved the source code to your working directory:

``cp $METPLOTPY_SOURCE/METplotpy/test/roc_diagram/custom_roc_diagram.yaml $WORKING_DIR/custom_roc_diagram.yaml``


Modify the `stat_input` and `plot_filename` settings in the
$METPLOTPY_SOURCE/METplotpy/test/roc_diagram/custom_roc_diagram.yaml
file to explicitly point to the $METPLOTPY_SOURCE/METplotpy/test/roc_diagram/roc_diagram directory (where
the custom config files and sample data reside).  Replace the relative path `./plot_20200507_074426.data`
with the full path `$WORKING_DIR/METplotpy/test/roc_diagram/plot_20200507_074426.data`

For example:

`stat_input: /username/working_dir/METplotpy/test/roc_diagram/plot_20200507_074426.data`

`plot_filename: /username/working_dir/output_plots/roc_diagram_custom.png`

where $WORKING_DIR was replaced with the actual name of the directory.  In this example, the
/username/working_dir/output_plots directory exists and has the appropriate read and write permissions.


If you wish to save the intermediate `.points1` file (used by METviewer but also useful for debugging), set the following configuration values:

`dump_points_1 setting: 'True'`

And add this line (anywhere in the file) if it doesn't already exist, to set the optional points_path:

`points_path: '/dir_to_save_points1_file'`


Replace the `'/dir_to_save_points1_file'` to the directory where you wish to save the file.


**Using defaults**

If you wish to use the **default** settings defined in the roc_diagram_defaults.yaml
file, specify a minimal custom configuration file (minimal_roc_diagram_defaults.yaml), which consists of only a comment
block, but can be any empty file:

.. literalinclude:: ../../test/roc_diagram/minimal_roc_diagram.yaml

copy this file to your working directory:

``cp $METPLOTPY_SOURCE/METplotpy/test/roc_diagram/minimal_roc_diagram.yaml $WORKING_DIR/minimal_roc_diagram.yaml``

Add the `stat_input` (input data) and `plot_filename` (output file/plot) settings to the $WORKING_DIR/minimal_roc_diagram.yaml
file (anywhere below the comment block). This explicitly indicates where the
sample data and custom configuration files are located.  Set the `stat_input` to
`$METPLOTPY_SOURCE/METplotpy/test/roc_diagram/plot_20200507_074426.data` and set the
`plot_filename` to  $WORKING_DIR/output_plots/roc_diagram_default.png:

`stat_input: $METPLOTPY_SOURCE/METplotpy/test/roc_diagram/plot_20200507_074426.data`

`plot_filename: $WORKING_DIR/output_plots/roc_diagram_default.png`

Where `$WORKING_DIR` is the working directory where you are saving all your custom
configuration files. **NOTE**: You may specify the `plot_filename` (output directory) to a directory other than the
$WORKING_DIR/output_plots, as long as it is an existing directory where you have read and write permissions.

If you wish to save the intermediate `.points1` file (used by METviewer and useful for debugging), add the following lines to your minimal_roc_diagram.yaml
file (anywhere below the comment block):

`dump_points_1: 'True'`

`points_path: '/dir_to_save_points1_file'`


Replace the `'/dir_to_save_points1_file'` to the directory where you wish to save the `.points1` file.
Make sure that this directory exists and has the appropriate read and write permissions.


Run from the Command Line
~~~~~~~~~~~~~~~~~~~~~~~~~

The ROC diagram plot that uses only the default values defined in
the roc_diagram_defaults.yaml configuration file looks like the following:

.. image:: roc_diagram_default.png


Perform the following:

* if using a conda environment, verify that you are running in the conda environment that
  has the required Python packages outlined in the requirements
  section

* cd to the $METPLOTPY_SOURCE/METplotpy/metplotpy/plots/roc_diagram
  directory

To generate the above **"defaults"** plot (i.e using default configuration settings), use the "minimal" custom configuration file, minimal_roc_diagram.yaml.

* enter the following command:

  ``python roc_diagram.py $WORKING_DIR/minimal_roc_diagram.yaml``


* a `roc_diagram_default.png` output file will be created in the
  directory you specified in the `plot_filename` configuration setting in the `roc_diagram_defaults.yaml` config file.

To generate a **customized** ROC diagram (i.e. some or all default configuration settings are
to be overridden), use the `custom_roc_diagram.yaml` config file.

* enter the following command:

``python roc_diagram.py $WORKING_DIR/custom_roc_diagram.yaml``

In this example, this custom config file changes the title and axis labels.

.. image:: roc_diagram_custom.png

* This plot is saved in the directory you specified in the `plot_filename` config setting in the custom roc_diagram.yaml config file.










