Reliability Diagram
===================

Description
~~~~~~~~~~~
Reliability diagrams are useful in displaying the conditional bias of probabilistic forecasts.
For more information about reliability diagrams, refer to the METviewer documentation:

https://dtcenter.github.io/METviewer/latest/Users_Guide/reliabilityplots.html

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
the first is a default configuration file, line_defaults.yaml that is found in the
$METPLOTPY_SOURCE/METplotpy/metplotpy/plots/config directory.  All default
configuration files are located in the $METPLOTPY_SOURCE/METplotpy/metplotpy/plots/config
directory.  Note, $METPLOTPY_SOURCE is the user-specified directory
where the METplotpy source code has been saved.  The second required YAML configuration file is a
user-supplied "custom" configuration file that is used to customize/override the default
settings in the line_defaults.yaml file.  The custom configuration file can be an empty
file if all default settings are to be applied.

METplus Configuration
~~~~~~~~~~~~~~~~~~~~~


**Default Configuration File**

The following is the `mandatory`, reliability_defaults.yaml configuration file,
which serves as a good starting point for creating a line
plot as it represents the default values set in METviewer

.. literalinclude:: ../../metplotpy/plots/config/reliability_defaults.yaml

**Custom Configuration File**

A second, `mandatory` configuration file is required, which is
used to customize the settings to the line plot. The custom_line.yaml
file is included with the source code.  If the user
wishes to use all the default settings defined in the line_defaults.yaml
file, an empty custom configuration file can be specified instead.

.. literalinclude:: ../../metplotpy/plots/reliability_diagram/custom_reliability.yaml



Run from the Command Line
~~~~~~~~~~~~~~~~~~~~~~~~~

The custom_reliability.yaml configuration file, in combination with the
line_defaults.yaml configuration file, generate a plot of
five series:

.. image:: custom_reliability_diagram.png

To generate the above plot using the reliability_defaults.yaml and
custom_reliability.yaml config files, perform the following:

* verify that you are running in the conda environment that
  has the required Python packages outlined in the requirements
  section

* cd to the $METPLOTPY_SOURCE/METplotpy/metplotpy/plots/reliability_diagram
  directory

* enter the following command:

  ``python reliability.py ./custom_reliability.yaml``


* a `custom_reliability_diagram.png` output file will be created in the
  $METPLOTPY_SOURCE/METplotpy/metplotpy/plots/reliability_diagram directory, as
  specified by the custom_reliability.yaml `plot_filename` value.
