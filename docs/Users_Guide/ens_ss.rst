**************************
Ensemble spread-skill plot
**************************

Description
===========
The theory is that RMSE of the ensemble mean should have roughly a 1-1 relationship
with the ensemble spread (I.e. standard deviation of the ensemble member values).
Ensemble spread-skill plot measures that relationship.

Example
=======

Sample Data
___________

The sample data used to create an example Ensemble spread-skill plot is available in the METplotpy
repository, where the Ensemble spread-skill plot tests are located:

$METPLOTPY_SOURCE/METplotpy/metplotpy/test/ens_ss/ens_ss.data

$METPLOTPY_SOURCE is the directory where the METplotpy code is saved.  The data is text
output from MET in columnar format.



Configuration Files
___________________

The Ensemble spread-skill plot utilizes YAML configuration files to indicate where input data is located and
to set plot attributes. These plot attributes correspond to values that can be set via the METviewer
tool. YAML is a recursive acroynym for "YAML Ain't Markup Language" and according to yaml.org,
it is a "human-readable data-serialization language". It is commonly used for configuration files
and in applications where data is being stored or transmitted".  Two configuration files are required,
the first is a default configuration file, bar_defaults.yaml that is found in the
$METPLOTPY_SOURCE/METplotpy/metplotpy/plots/config directory.  All default
configuration files are located in the $METPLOTPY_SOURCE/METplotpy/metplotpy/plots/config
directory.  Note, $METPLOTPY_SOURCE is the user-specified directory
where the METplotpy source code has been saved.  The second required YAML configuration file is a
user-supplied "custom" configuration file that is used to customize/override the default
settings in the bar_defaults.yaml file.  The custom configuration file can be an empty
file if all default settings are to be applied.


METplus Configuration
=====================

Default Configuration File
__________________________

The following is the `mandatory`, bar_defaults.yaml configuration file,
which serves as a good starting point for creating a line
plot as it represents the default values set in METviewer

.. literalinclude:: ../../metplotpy/plots/config/ens_ss_defaults.yaml

Custom Configuration File
_________________________

A second, `mandatory` configuration file is required, which is
used to customize the settings to the bar plot. The custom_bar.yaml
file is included with the source code.  If the user
wishes to use all the default settings defined in the bar_defaults.yaml
file, an empty custom configuration file can be specified instead.

.. literalinclude:: ../../test/ens_ss/custom_ens_ss.yaml



Run from the Command Line
=========================

The custom_bar.yaml configuration file, in combination with the
bar_defaults.yaml configuration file, generate a plot of
five four:

.. image:: ens_ss.png

To generate the above plot using the bar_defaults.yaml and
custom_bar.yaml config files, perform the following:

* verify that you are running in the conda environment that
  has the required Python packages outlined in the requirements
  section

* provide the absolute path to the stat_input property from the custom_line.yaml

* cd to the $METPLOTPY_SOURCE/METplotpy/metplotpy/plots/ens_ss
  directory

* enter the following command:

  ``python ens_ss.py <path_to>custom_ens_ss.yaml``


* a `ens_ss.png` output file will be created in the
  $METPLOTPY_SOURCE/METplotpy/metplotpy/plots/ens_ss directory, as
  specified by the custom_ens_ss.yaml `plot_filename` value.

* in addition, a ens_ss.point1 (<outputfilename>.point1) text file is also
  generated, which lists the statistics used to create the plot(s).  This
  information can be useful in debugging.

