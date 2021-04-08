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
directory.  Note, $METPLOTPY_SOURCE is the user-specified directory
where the METplotpy source code has been saved.  The second required YAML configuration file is a
user-supplied "custom" configuration file that is used to customize/override the default
settings in the reliability_defaults.yaml file.  The custom configuration file can be an empty
file if all default settings are to be applied.

METplus Configuration
~~~~~~~~~~~~~~~~~~~~~


**Default Configuration File**

The following is the `mandatory`, reliability_defaults.yaml configuration file,
which serves as a good starting point for creating a reliability diagram
plot as it represents the default values set in METviewer

.. literalinclude:: ../../metplotpy/plots/config/reliability_defaults.yaml

**Custom Configuration File**

A second, `mandatory` configuration file is required, which is
used to customize the settings to the reliability diagram plot. The custom_reliability.yaml
file is included with the source code an looks like the following:

.. literalinclude:: ../../metplotpy/plots/reliability_diagram/custom_reliability_diagram.yaml

If the user
wishes to use all the default settings defined in the reliability_defaults.yaml
file, an empty custom configuration file (custom_reliability_use_defaults.yaml)
can be specified instead:

.. literalinclude:: ../../metplotpy/plots/reliability_diagram/custom_reliability_use_defaults.yaml



Run from the Command Line
~~~~~~~~~~~~~~~~~~~~~~~~~

The reliability diagram plot that uses only the default values defined in
the reliability_defaults.yaml configuration file looks like the following:

.. image:: default_reliability_diagram.png


To generate the above plot, use the reliability_defaults.yaml and
the empty custom configuration file, custom_reliability_use_defaults.yaml config files.
Then, perform the following:

* verify that you are running in the conda environment that
  has the required Python packages outlined in the requirements
  section

* cd to the $METPLOTPY_SOURCE/METplotpy/metplotpy/plots/reliability_diagram
  directory

* enter the following command:

  ``python reliability.py ./custom_reliability_use_defaults.yaml``


* a `default_reliability_diagram.png` output file will be created in the
  $METPLOTPY_SOURCE/METplotpy/metplotpy/plots/reliability_diagram directory. The filename is
  specified by the `plot_filename` value in the reliability_defaults.yaml config file.

To generate a customized reliability diagram, use the custom_reliability_diagram.yaml config
file.

* enter the following command:

``python reliability.py ./custom_reliability_diagram.yaml``

In this example, this custom config file changes the color of the boxes.

.. image:: custom_reliability_diagram.png

* in addition, a line.point1 (<outputfilename>.point1) text file is also
  generated, which lists the independent and dependent variables that
  are plotted.  This information can be useful in debugging.


