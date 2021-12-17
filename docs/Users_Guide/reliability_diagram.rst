Reliability Diagram
===================

Description
~~~~~~~~~~~
Reliability diagrams are useful in displaying the conditional bias of probabilistic forecasts.
For more information about reliability diagrams, refer to the METviewer documentation:

https://metviewer.readthedocs.io/en/latest/Users_Guide/reliabilityplots.html

Example
~~~~~~~

**Sample Data**

The sample data used to create an example reliability diagram is available in the METplotpy
repository, where the reliabilty diagram code is located:

$METPLOTPY_SOURCE/METplotpy/metplotpy/test/reliability_diagram/plot_20210311_145053.data

$METPLOTPY_SOURCE is the directory where the METplotpy code is saved.  The data is text
output from MET in columnar format.


**Configuration Files**

The reliability diagram utilizes YAML configuration files to indicate where input data is located and
to set plot attributes. These plot attributes correspond to values that can be set via the METviewer
tool. YAML is a recursive acroynym for "YAML Ain't Markup Language" and according to yaml.org,
it is a "human-readable data-serialization language". It is commonly used for configuration files
and in applications where data is being stored or transmitted".  Two configuration files are required,
the first is a default configuration file, reliability_defaults.yaml that is found in the
$METPLOTPY_SOURCE/METplotpy/metplotpy/plots/config directory.  All default
configuration files are located in the $METPLOTPY_SOURCE/METplotpy/metplotpy/plots/config
directory. Note, $METPLOTPY_SOURCE is the user-specified directory
where the METplotpy source code has been saved.  **Default configuration files are automatically loaded by the plotting code and do not
need to be explicitly specified when generating a plot**.  The second required YAML configuration file is a
user-supplied "custom" configuration file that is used to customize/override the default
settings in the reliability_defaults.yaml file.  The custom configuration file can be an empty
file if all default settings are to be applied.

METplotpy Configuration
~~~~~~~~~~~~~~~~~~~~~~~


**Default Configuration File**

The following is the `mandatory`, reliability_defaults.yaml configuration file,
which serves as a starting point for creating a reliability diagram
plot as it represents the default values set in METviewer

**NOTE**: This default configuration file is automatically loaded by reliability_diagram.py.

.. literalinclude:: ../../metplotpy/plots/config/reliability_defaults.yaml

**Custom Configuration File**

A second, `mandatory` configuration file is required, which is
used to customize the settings to the reliability diagram plot. The custom_reliability.yaml
file is included with the source code and looks like the following:

.. literalinclude:: ../../test/reliability_diagram/custom_reliability_diagram.yaml

Copy this custom config file from the directory where you saved the source code to your working directory:

``cp $METPLOTPY_SOURCE/METplotpy/test/reliability_diagram/custom_reliability_diagram.yaml $WORKING_DIR/custom_reliability_diagram.yaml``


Modify the `stat_input` setting in the
$METPLOTPY_SOURCE/METplotpy/test/reliability_diagram/custom_reliability_diagram.yaml
file to explicitly point to the $METPLOTPY_SOURCE/METplotpy/test/reliability_diagram/reliability_diagram directory (where
the custom config files and sample data reside).  Replace the relative path `./plot_20210311_145053.data`
with the full path `$WORKING_DIR/METplotpy/test/reliability_diagram/plot_20210311_145053.data`.  Modify the
`plot_filename` setting to point to the output path where your plot will be saved, including the name of your plot.

For example:

`stat_input: /username/myworkspace/METplotpy/test/reliability_diagram/plot_20210311_145053.data`

`plot_filename: /username/working_dir/output_plots/reliability_diagram_custom.png`

where /username/myworkspace/ is $METPLOTPY_SOURCE and /username/working_dir is $WORKING_DIR.  Make sure that the
$WORKING_DIR directory you specify exists and has the appropriate read and write permissions.  You may
change the path listed for `plot_filename` to the output directory of your choice.  If this is not set, then the
`plot_filename` setting specified in the $METPLOTPY_SOURCE/METplotpy/metplotpy/plots/config/reliability_diagram_defaults.yaml
configuration file will be used.

If you wish to save the intermediate `.points1` file (used by METviewer and useful for debugging), set the `dump_points_1`
setting to True.  Uncomment or add (if it doesn't exist) the `points_path` setting:

`dump_points_1: 'True'`

`points_path: '/dir_to_save_points1_file'`

Replace the `'/dir_to_save_points1_file'` to the directory where you wish to save the `.points1` file. If points_path
is commented out (indicated by a '#' symbol in front of it), remove the '#' symbol to uncomment
the points_path so that it will be used by the code.  Make sure that this directory exists and has the
appropriate read and write permissions.  **NOTE**: the `points_path` setting
is **optional** and does not need to be defined in your configuration file unless you wish to save the
intermediate .points1 file.


**Using defaults**

If the user wishes to use all the default settings defined in the reliability_defaults.yaml
file, an empty custom configuration file (custom_reliability_use_defaults.yaml)
can be specified (as long you have write permissions for the output filename path corresponding to the
`plot_filename` setting in the default configuration file. Otherwise you will need to specify a `plot_filename` in your minimal_box.yaml file):

.. literalinclude:: ../../metplotpy/plots/reliability_diagram/custom_reliability_use_defaults.yaml

Copy this file to your working directory:

``cp $METPLOTPY_SOURCE/METplotpy/test/reliability_diagram/minimal_reliability_diagram.yaml
$WORKING_DIR/minimal_reliability_diagram.yaml``

Add the `stat_input` (input data) and `plot_filename` (output file/plot) settings to the $WORKING_DIR/minimal_reliability_diagram.yaml
file (anywhere below the comment block). The `stat_input` setting explicitly indicates where the
sample data and custom configuration files are located.

Set the `stat_input` to
`$METPLOTPY_SOURCE/METplotpy/test/reliability_diagram/plot_20210311_145053.data`
and set the `plot_filename` to $WORKING_DIR/output_plots/reliability_diagram_default.png:

`stat_input: $METPLOTPY_SOURCE/METplotpy/test/reliability_diagram/plot_20210311_145053.data`

`plot_filename: $WORKING_DIR/output_plots/reliability_diagram_default.png`

Where `$WORKING_DIR` is the working directory where you are saving all your custom
configuration files. **NOTE**: You may specify the `plot_filename` (output directory) to a directory other than the
$WORKING_DIR/output_plots, as long as it is an existing directory where you have read and write permissions.

If you wish to save the intermediate `.points1` file (used by METviewer and useful for debugging), add the following
lines to your minimal_reliability_diagram.yaml file (anywhere below the comment block):

`dump_points_1: 'True'`

`points_path: '/dir_to_save_points1_file'`


Replace the `'/dir_to_save_points1_file'` to the directory where you wish to save the `.points1` file.
Make sure that this directory exists and has the appropriate read and write permissions. **NOTE**: the `points_path` setting
is **optional** and does not need to be defined in your configuration file unless you wish to save the intermediate .points1
file.


Run from the Command Line
~~~~~~~~~~~~~~~~~~~~~~~~~

The reliability diagram plot that uses only the default values defined in
the reliability_defaults.yaml configuration file looks like the following:

.. image:: default_reliability_diagram.png


To generate the above plot, you will use the reliability_defaults.yaml and
the "empty", custom configuration file, custom_reliability_use_defaults.yaml config file.

Perform the following:

* clone the code from the METplotpy repository at github.com/dtcenter/METplotpy:

``cd $METPLOTPY_SOURCE``

``git clone https://github.com/dtcenter/METplotpy``



* if using a conda environment, verify that you are running in the conda environment that
  has the required Python packages outlined in the requirements
  section


* set the METPLOTPY_BASE environment variable to point to $METPLOTPY_SOURCE/METplotpy/metplotpy

for ksh:

``export METPLOTPY_BASE=$METPLOTPY_SOURCE/METplotpy/metplotpy``

for csh:

``setenv METPLOTPY_BASE $METPLOTPY_SOURCE/METplotpy/metplotpy``

Replacing the $METPLOTPY_SOURCE with the directory where the METplotpy source code was saved.


* enter the following command:

  ``python $METPLOTPY_SOURCE/METplotpy/metplotpy/plots/reliability_diagram/reliability.py $WORKING_DIR/custom_reliability_use_defaults.yaml``


* a `default_reliability_diagram.png` output file will be created in the
  directory you specified in the `plot_filename` configuration setting in the `minimal_reliability.yaml` config file.
  The filename is specified by the `plot_filename` value in the reliability_defaults.yaml config file.

To generate a **customized** reliability diagram (i.e. some or all default configuration settings are
to be overridden), use the custom_reliability_diagram.yaml config file.

* enter the following command:

``python $METPLOTPY_SOURCE/METplotpy/metplotpy/plots/reliability_diagram/reliability.py $WORKING_DIR/custom_reliability_diagram.yaml``

In this example, this custom config file changes the color of the boxes.

.. image:: custom_reliability_diagram.png

* a custom_reliability_diagram.png output file will be created in the directory you specified in the `plot_filename` configuration setting in the custom_reliability_diagram.yaml config file.



