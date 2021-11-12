*********
Line Plot
*********

Description
===========
The line plot is a scatter plot where each point is connected by a line.
It is used by METviewer for generating series plots.
Refer to the METviewer documentation for details on how this
plot is utilized:

https://metviewer.readthedocs.io/en/latest/Users_Guide/seriesplots.html


Example
=======

Sample Data
___________

The sample data used to create an example line plot is available in the
*METplotpy* repository, where the line plot tests are located:

*$METPLOTPY_SOURCE/METplotpy/metplotpy/test/line/line.data*

*$METPLOTPY_SOURCE* is the directory where the METplotpy code is saved.
The data is text output from MET in columnar format.



Configuration Files
___________________

The line plot utilizes YAML configuration files to indicate where input
data is located and to set plot attributes. These plot attributes correspond
to values that can be set via the METviewer tool. YAML is a recursive
acronym for "YAML Ain't Markup Language" and according to
`yaml.org <yaml.org>`_, it is a "human-readable data-serialization language".
It is commonly used for configuration files and in applications where
data is being stored or
transmitted.  Two configuration files are required, the first is a default
configuration file, **line_defaults.yaml** that is found in the
*$METPLOTPY_SOURCE/METplotpy/metplotpy/plots/config* directory.  All default
configuration files are located in the
*$METPLOTPY_SOURCE/METplotpy/metplotpy/plots/config*
directory.  Note, *$METPLOTPY_SOURCE* is the user-specified directory
where the METplotpy source code has been saved.  The second required YAML
configuration file is a user-supplied "custom" configuration file that is
used to customize/override the default settings in the
**line_defaults.yaml** file.  The custom configuration file can be an empty
file if all default settings are to be applied.


METplus Configuration
=====================

Default Configuration File
__________________________

The following is the `mandatory`, **line_defaults.yaml** configuration file,
which serves as a good starting point for creating a line
plot as it represents the default values set in METviewer

.. literalinclude:: ../../metplotpy/plots/config/line_defaults.yaml

Custom Configuration File
_________________________

A second, `mandatory` configuration file is required, which is
used to customize the settings to the line plot. The **custom_line.yaml**
file is included with the source code.  If the user
wishes to use all the default settings defined in the **line_defaults.yaml**
file, an empty custom configuration file can be specified instead.

.. literalinclude:: ../../metplotpy/plots/line/custom_line.yaml



Run from the Command Line
=========================

The **custom_line.yaml** configuration file, in combination with the
**line_defaults.yaml** configuration file, generate a plot of
five series:

.. image:: line.png

To generate the above plot using the **line_defaults.yaml** and
**custom_line.yaml** config files, perform the following:

* Verify the conda environment is running and has
  has the required Python packages outlined in the requirements
  section.

* Change directories on the command line:

.. code-block:: ini

  cd  $METPLOTPY_SOURCE/METplotpy/metplotpy/plots/line

* Enter the following command:

.. code-block:: ini
    
  python line.py ./custom_line.yaml


* A **line.png** output file will be created in the
  *$METPLOTPY_SOURCE/METplotpy/metplotpy/plots/line* directory, as
  specified by the **custom_line.yaml plot_filename** value.

* in addition, a **line.point1 (<outputfilename>.point1)** text file is also
  generated, which lists the independent and dependent variables that
  are plotted.  This information can be useful in debugging.
