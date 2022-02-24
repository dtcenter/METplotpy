*******************
Performance Diagram
*******************

Description
===========

Performance diagrams are used to show the relationship between categorical
statistics, with  axes representing detection and success (1 - false alarm)
rates (:ref:`Roebber, 2009<Roebber>`).  
The simplest input to the performance diagram is the MET contingency
table statistics (CTS)  output.  This output can be produced by many of
the MET tools (Point-Stat, Grid-Stat, etc.)
For more information on Performance diagrams, please refer to the
`METviewer documentation
<https://metviewer.readthedocs.io/en/latest/Users_Guide/perfdiag.html>`_.

There are several reference lines on the performance diagram.  The dashed
lines that radiate from the origin are lines of equal frequency bias.
Labels for the frequency bias amount are at the end of each line. The
diagonal represents a perfect frequency bias score of 1.  Curves of
equal Critical Success Index (CSI) connect the top of the plot to the
right side.  CSI amounts are listed to the right side of the plot,
with better values falling closer to the top.

.. image:: performance_diagram_default.png

Example
=======

Sample Data
___________

The sample data used to create these plots is available in the METplotpy
repository, where the performance diagram scripts are located:

*$METPLOTPY_SOURCE/METplotpy/test/performance_diagram/plot_20200317_151252.data*

*$METPLOTPY_SOURCE* is the directory where the METplotpy code is saved.
The data is text output from MET in columnar format.

Configuration Files
___________________

The performance diagram utilizes YAML configuration files to indicate where
input data is located and to set plot attributes. These plot attributes
correspond to values that can be set via the METviewer tool. YAML is a
recursive acronym for "YAML Ain't Markup Language" and according to
`yaml.org <https://yaml.org>`_,
it is a "human-friendly data serialization language. It is commonly used for
configuration files and in applications where data is being stored or
transmitted. Two configuration files are required. The first is a
default configuration file, **performance_diagram_defaults.yaml**,
which is found in the
*$METPLOTPY_SOURCE/METplotpy/metplotpy/plots/config* directory.
*$METPLOTPY_SOURCE* indicates the directory where the METplotpy
source code has been saved.  All default
configuration files are located in the
*$METPLOTPY_SOURCE/METplotpy/metplotpy/plots/config* directory.
**Default configuration files are automatically loaded by the
plotting code and do not need to be explicitly specified when
generating a plot**.

The second required configuration file is a user-supplied “custom”
configuration file. This  file is used to customize/override the default
settings in the **performance_diagram_defaults.yaml** file. The custom
configuration file can be an empty file if all default settings are to
be applied.

METplus Configuration
=====================

Default Configuration File
__________________________

The following is the *mandatory*, **performance_diagram_defaults.yaml**
configuration file, which serves as a starting point for creating a
performance diagram plot,  as it represents the default values set in METviewer.

**NOTE**: This default configuration file is automatically loaded by
**performance_diagram.py.**


.. literalinclude:: ../../metplotpy/plots/config/performance_diagram_defaults.yaml

Custom Configuration File
_________________________

A second, *mandatory* configuration file is required, which is
used to customize the settings to the performance diagram plot.
The **custom_performance_diagram.yaml**  file is included with the
source code and looks like the following:

.. literalinclude:: ../../test/performance_diagram/custom_performance_diagram.yaml

Copy this custom config file from the directory where the source
code was saved to the working directory:

.. code-block:: ini

  cp $METPLOTPY_SOURCE/METplotpy/test/performance_diagram/custom_performance_diagram.yaml $WORKING_DIR/custom_performance_diagram.yaml

Modify the *stat_input* setting in the
*$METPLOTPY_SOURCE/METplotpy/test/performance_diagram/custom_performance_diagram.yaml*
file to explicitly point to the
*$METPLOTPY_SOURCE/METplotpy/test/performance_diagram/performance_diagram*
directory (where the custom config files and sample data reside).
Replace the relative path *./plot_20200317_151252.data*
with the full path
*$METPLOTPY_SOURCE/METplotpy/test/performance_diagram/plot_20200317_151252.data*.
Modify the *plot_filename* setting to point to the output path where the
plot will be saved, including the name of the plot.

For example:

*stat_input: /username/myworkspace/METplotpy/test/performance_diagram/plot_20200317_151252.data*

*plot_filename: /username/working_dir/output_plots/performance_diagram_custom.png*

This is where */username/myworkspace/* is $METPLOTPY_SOURCE and
*/username/working_dir* is $WORKING_DIR.  Make sure that the
$WORKING_DIR directory that is specified exists and has the
appropriate read and write permissions. The path listed for
*plot_filename* may be changed to the output directory of one’s choosing.
If this is not set, then the
*plot_filename* setting specified in the
*$METPLOTPY_SOURCE/METplotpy/metplotpy/plots/config/performance_diagram_defaults.yaml*
configuration file will be used.

To save the intermediate **.points1** file (used by METviewer and useful
for debugging), set the *dump_points_1* setting to True.
Uncomment or add (if it doesn't exist) the *points_path* setting:

*dump_points_1: 'True'*

*points_path: '/dir_to_save_points1_file'*

Replace the */dir_to_save_points1_file* to the same directory where the
**.points1** file is saved.
If *points_path* is commented out (indicated by a '#' symbol in front of it),
remove the '#' symbol to uncomment
the *points_path* so that it will be used by the code.  Make sure that
this directory exists and has the
appropriate read and write permissions.  **NOTE**: the *points_path* setting
is **optional** and does not need to be defined in the configuration
file unless saving the intermediate **.points1** file is desired.

Using defaults
______________

To use the *default* settings defined in the
**performance_diagram_defaults.yaml**
file, specify a minimal custom configuration file
(**minimal_performance_diagram_defaults.yaml**), which consists of only
a comment block, but it can be any empty file (write permissions for the
output filename path corresponding to the *plot_filename* setting in
the default configuration file will be needed. Otherwise, specify
a *plot_filename* in the **minimal_performance_diagram.yaml** file):

.. literalinclude:: ../../test/performance_diagram/minimal_performance_diagram.yaml

Copy this file to the working directory:

.. code-block:: ini
		
  cp $METPLOTPY_SOURCE/METplotpy/test/performance_diagram/minimal_performance_diagram.yaml $WORKING_DIR/minimal_performance_diagram.yaml

Add the *stat_input* (input data) and *plot_filename*
(output file/plot path) settings to the
*$WORKING_DIR/minimal_performance_diagram.yaml*
file (anywhere below the comment block). The *stat_input* setting
explicitly indicates where the sample data and custom configuration
files are located.  Set the *stat_input* to
*$METPLOTPY_SOURCE/METplotpy/test/performance_diagram/plot_20200317_151252.data* and set the
*plot_filename* to
*$WORKING_DIR/output_plots/performance_diagram_default.png*:

*stat_input: $METPLOTPY_SOURCE/METplotpy/test/performance_diagram/plot_20200317_151252.data*

*plot_filename: $WORKING_DIR/output_plots/performance_diagram_default.png*

*$WORKING_DIR* is the working directory where all of
the custom configuration files are being saved.
**NOTE**: The *plot_filename* (output directory) may be specified
to a directory other than the *$WORKING_DIR/output_plots*, as long as
it is an existing directory where the author has read and write permissions.

To save the intermediate **.points1** file (used by METviewer and useful
for debugging), add the following lines to the
**minimal_performance_diagram.yaml** file (anywhere below the comment block):

*dump_points_1: 'True'*

*points_path: '/dir_to_save_points1_file'*


Replace the */dir_to_save_points1_file* to the same directory where
the **.points** file is saved. Make sure that this directory exists
and has the appropriate read and write permissions.

Run from the Command Line
=========================

To generate a default performance diagram (i.e. using settings in the 
**performance_diagram_defaults.yaml** configuration file),
perform the following:


*  If using the conda environment, verify the conda environment
   is running and has has the required Python packages outlined in the
   `requirements section.
   <https://metplotpy.readthedocs.io/en/latest/Users_Guide/installation-requirements.html>`_

* Set the METPLOTPY_BASE environment variable to point to
  *$METPLOTPY_SOURCE/METplotpy*.

  For the ksh environment:

  .. code-block:: ini
		
    export METPLOTPY_BASE=$METPLOTPY_SOURCE/METplotpy

  For the csh environment:

  .. code-block:: ini
		
    setenv METPLOTPY_BASE $METPLOTPY_SOURCE/METplotpy

  Replacing the $METPLOTPY_SOURCE with the directory where the
  METplotpy source code was saved.

* Run the following on the command line:

  .. code-block:: ini  

    python $METPLOTPY_SOURCE/METplotpy/metplotpy/plots/performance_diagram/performance_diagram.py $WORKING_DIR/minimal_performance_diagram.yaml

  This will create a PNG file, **performance_diagram_default.png**,
  in the directory that was specified in the *plot_filename*
  setting of the **minimal_performance_diagram.yaml** config file:

  .. image:: performance_diagram_default.png

  To generate a slightly modified, **customized** plot, re-run the above
  command using the **custom_performance_diagram.yaml** file:

  .. code-block:: ini
		
    python $METPLOTPY_SOURCE/METplotpy/metplotpy/plots/performance_diagram/performance_diagram.py $WORKING_DIR/custom_performance_diagram.yaml

  .. image:: performance_diagram_custom.png

* A **performance_diagram_custom.png** output file will be created in
  the directory that was  specified in the *plot_filename* config setting
  in the **custom_performance_diagram.yaml** config file.
