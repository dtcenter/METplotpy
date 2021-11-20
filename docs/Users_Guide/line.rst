Line plot
===========================================

Description
~~~~~~~~~~~
The line plot is a scatter plot where each point is connected by a line.
It is used by METviewer for generating series plots.
Refer to the METviewer documentation for details on how this
plot is utilized:

https://metviewer.readthedocs.io/en/latest/Users_Guide/seriesplots.html


Example
~~~~~~~

**Sample Data**

The sample data used to create an example line plot is available in the METplotpy
repository, where the line plot tests are located:

$METPLOTPY_SOURCE/METplotpy/metplotpy/test/line/line.data

$METPLOTPY_SOURCE is the directory where the METplotpy code is saved (e.g. /username/myworkspace)..  The data is text
output from MET in columnar format.



**Configuration Files**

The line plot utilizes YAML configuration files to indicate where input data is located and
to set plot attributes. These plot attributes correspond to values that can be set via the METviewer
tool. YAML is a recursive acroynym for "YAML Ain't Markup Language" and according to yaml.org,
it is a "human-readable data-serialization language". It is commonly used for configuration files
and in applications where data is being stored or transmitted".  Two configuration files are required,
the first is a default configuration file, line_defaults.yaml that is found in the
$METPLOTPY_SOURCE/METplotpy/metplotpy/plots/config directory.  All default
configuration files are located in the $METPLOTPY_SOURCE/METplotpy/metplotpy/plots/config
directory.  $METPLOTPY_SOURCE is the user-specified directory
where the METplotpy source code has been saved. **Default configuration files are automatically loaded by the plotting code and do not
need to be explicitly specified when generating a plot**. The second required YAML configuration file is a
user-supplied "custom" configuration file that is used to customize/override the default
settings in the line_defaults.yaml file.  The custom configuration file can be an empty
file if all default settings are to be applied.


METplus Configuration
~~~~~~~~~~~~~~~~~~~~~

**Default Configuration File**

The following is the `mandatory`, line_defaults.yaml configuration file,
which serves as a good starting point for creating a line
plot as it represents the default values set in METviewer

**NOTE**: This default configuration file is automatically loaded by line.py

.. literalinclude:: ../../metplotpy/plots/config/line_defaults.yaml

**Custom Configuration File**

A second, `mandatory` configuration file is required, which is
used to customize the settings to the line plot. The custom_line.yaml
file is included with the source code.  If the user
wishes to use all the default settings defined in the line_defaults.yaml
file, an empty custom configuration file can be specified instead.

.. literalinclude:: ../../test/line/custom_line.yaml

Copy this custom config file from the directory where you saved the source code to your working directory:

``cp $METPLOTPY_SOURCE/METplotpy/test/line/custom_line.yaml $WORKING_DIR/custom_line.yaml``

Modify the `stat_input` setting in the
$METPLOTPY_SOURCE/METplotpy/test/line/custom_line.yaml
file to explicitly point to the $METPLOTPY_SOURCE/METplotpy/test/line directory (where
the custom config files and sample data reside).  Replace the relative path `./line.data`
with the full path `$METPLOTPY_SOURCE/METplotpy/test/line/line.data`.  Modify the `plot_filename`
setting to point to the output path where your plot will be saved, including the name of your plot.

For example:

`stat_input: /username/myworkspace/METplotpy/test/line/line.data`

`plot_filename: /username/working_dir/output_plots/line.png`

where /username/myworkspace/ is $METPLOTPY_SOURCE and /username/working_dir is $WORKING_DIR.  Make sure that the
$WORKING_DIR directory you specify exists and has the appropriate read and write permissions.  You may
change the path listed for `plot_filename` to the output directory of your choice.  If this is not set, then the
`plot_filename` setting specified in the $METPLOTPY_SOURCE/METplotpy/metplotpy/plots/config/line_defaults.yaml
configuration file will be used.

If you wish to save the intermediate `.points1` file (used by METviewer and useful for debugging), set the `dump_points_1`
setting to True. Uncomment or add (if it doesn't exist) the `points_path` setting.

`dump_points_1: 'True'`

`points_path: '/dir_to_save_points1_file'`

Replace the `'/dir_to_save_points1_file'` to the directory where you wish to save the `.points1` file.
If points_path is commented out (indicated by a '#' symbol in front of it), remove the '#' symbol to uncomment
the points_path so that it will be used by the code.  Make sure that this directory exists and has the
appropriate read and write permissions.  **NOTE**: the `points_path` setting
is **optional** and does not need to be defined in your configuration file unless you wish to save the intermediate .points1
file.

**Using defaults**

If you wish to use the **default** settings defined in the line_defaults.yaml
file, specify a minimal custom configuration file (minimal_line.yaml), which consists of only a comment
block, but can be any empty file:

.. literalinclude:: ../../test/line/minimal_line.yaml

Copy this file to your working directory:

``cp $METPLOTPY_SOURCE/METplotpy/test/line/minimal_line.yaml $WORKING_DIR/minimal_line.yaml``

Add the `stat_input` (input data) and `plot_filename` (output file/plot path) settings to the $WORKING_DIR/minimal_line.yaml
file (anywhere below the comment block). The `stat_input` setting explicitly indicates where the
sample data and custom configuration files are located.  Set the `stat_input` to
`$METPLOTPY_SOURCE/METplotpy/test/line/line.data` and set the
`plot_filename` to $WORKING_DIR/output_plots/line_default.png:

`stat_input: $METPLOTPY_SOURCE/METplotpy/test/line/line.data`

`plot_filename: $WORKING_DIR/output_plots/line_default.png`

Where `$WORKING_DIR` is the working directory where you are saving all your custom
configuration files. **NOTE**: You may specify the `plot_filename` (output directory) to a directory other than the
$WORKING_DIR/output_plots, as long as it is an existing directory where you have read and write permissions.

**NOTE**: This default plot does not display any of the data points. It is to be used as a template for
setting up margins, captions, label sizes, etc.

Run from the Command Line
~~~~~~~~~~~~~~~~~~~~~~~~~

The custom_line.yaml configuration file, in combination with the
line_defaults.yaml configuration file, generates a plot of
five series:

.. image:: line.png

To generate the above plot using the line_defaults.yaml and
custom_line.yaml config files, perform the following:

* if using a conda environment, verify that you are running in the conda environment that
  has the required Python packages outlined in the Python Requirements
  section:

https://metplotpy.readthedocs.io/en/latest/Users_Guide/installation.html

* set the METPLOTPY_BASE environment variable to point to $METPLOTPY_SOURCE/METplotpy/metplotpy

for ksh:

``export METPLOTPY_BASE=$METPLOTPY_SOURCE/METplotpy/metplotpy``

for csh:

``setenv METPLOTPY_BASE $METPLOTPY_SOURCE/METplotpy/metplotpy``

Replacing the $METPLOTPY_SOURCE with the directory where the METplotpy source code was saved.

To generate the above **"defaults"** plot (i.e using default configuration settings), use the "minimal" custom configuration file, minimal_line.yaml.

* enter the following command:

  ``python line.py ./minimal_line.yaml``


* a `line_default.png` output file will be created in the
  directory you specified in the `plot_filename` configuration setting in the `line_defaults.yaml` config file.

To generate a **customized** line diagram (i.e. some or all default configuration settings are
to be overridden), use the `custom_line.yaml` config file.

* enter the following command:

``python $METPLOTPY_SOURCE/METplotpy/metplotpy/plots/line/line.py $WORKING_DIR/custom_line.yaml``

.. image:: line.png



