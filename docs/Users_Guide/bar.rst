Bar plot
===========================================

Description
~~~~~~~~~~~
A bar plot shows comparisons among discrete categories. One axis of the
chart shows the specific categories being compared, while the other
represents some measured value. The heights or lengths are proportional to
the values that they represent. Bar plots are simple and flexible, unlike
some other METview plot types. Rather than using prescribed statistics in
a specific way, the user can select both axes.

Bar plots are distinct from histograms and the two are not interchangeable.
Histograms show the frequency of occurrence of values in discrete
categories (that are sometimes created by binning continuous values).
To create a histogram, the user may only select the variable for a single
axis. In a bar plot, two axis values are selected by the user, one
categorical and one numeric.

Bar plots often represent counts or frequencies, however, bar plots can
represent means, medians, standard deviations, or any other statistic.
Refer to the METviewer documentation for details on how this
plot is utilized:

https://metviewer.readthedocs.io/en/latest/Users_Guide/barplot.html


Example
~~~~~~~

**Sample Data**

The sample data used to create an example bar plot is available in the METplotpy
repository, where the bar plot tests are located:

$METPLOTPY_SOURCE/METplotpy/metplotpy/test/bar/bar.data

$METPLOTPY_SOURCE is the directory where the METplotpy code is saved.  The data is text
output from MET in columnar format.



**Configuration Files**

The bar plot utilizes YAML configuration files to indicate where input data is located and
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
~~~~~~~~~~~~~~~~~~~~~

**Default Configuration File**

The following is the `mandatory`, bar_defaults.yaml configuration file,
which serves as a good starting point for creating a line
plot as it represents the default values set in METviewer

.. literalinclude:: ../../metplotpy/plots/config/bar_defaults.yaml

**Custom Configuration File**

A second, `mandatory` configuration file is required, which is
used to customize the settings to the bar plot. The custom_bar.yaml
file is included with the source code.  If the user
wishes to use all the default settings defined in the bar_defaults.yaml
file, an empty custom configuration file can be specified instead.

.. literalinclude:: ../../test/bar/custom_bar.yaml



Run from the Command Line
~~~~~~~~~~~~~~~~~~~~~~~~~

The custom_bar.yaml configuration file, in combination with the
bar_defaults.yaml configuration file, generate a plot of
five four:

.. image:: bar.png

To generate the above plot using the bar_defaults.yaml and
custom_bar.yaml config files, perform the following:

* verify that you are running in the conda environment that
  has the required Python packages outlined in the requirements
  section

* provide the absolute path to the stat_input property from the custom_line.yaml

* cd to the $METPLOTPY_SOURCE/METplotpy/metplotpy/plots/bar
  directory

* enter the following command:

  ``python bar.py <path_to>custom_bar.yaml``


* a `bar.png` output file will be created in the
  $METPLOTPY_SOURCE/METplotpy/metplotpy/plots/bar directory, as
  specified by the custom_bar.yaml `plot_filename` value.

* in addition, a bar.point1 (<outputfilename>.point1) text file is also
  generated, which lists the statistics used to create bars.  This information can be useful in debugging.

