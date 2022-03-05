*************
Contour Plots
*************

Description
===========

Contour plots are a very general plot type somewhat similar to a scatter
plot. The axes are specified by the user, and any will do so long as the
entire set of x and y locations has some value (i.e. not missing data). The
value is then contoured. This type of plot is often used to examine
statistics over a series of time or heights.
For more information on Contour plots, please refer to the
`METviewer documentation
<https://metviewer.readthedocs.io/en/latest/Users_Guide/contourplot.html>`_.



.. image:: contour.png

Example
=======

Sample Data
___________

The data is text output from MET in columnar format.
The sample data used to create these plots is available in the METplotpy
repository:

*$METPLOTPY_BASE/test/contour/contour.data*

*$METPLOTPY_BASE* is the directory where the METplotpy code is saved:

e.g.

*/usr/path/to/METplotpy*  if the source code was cloned or forked from the Github repository

or

*/usr/path/to/METplotpy-x.y.z*  if the source code was downloaded as a zip or gzip'd tar file from the Release link of
the Github repository.  The *x.y.z* is the release number.



Configuration Files
___________________

The contour plot utilizes YAML configuration files to indicate where
input data is located and to set plot attributes. These plot attributes
correspond to values that can be set via the METviewer tool. YAML is a
recursive acronym for "YAML Ain't Markup Language" and according to
`yaml.org <https://yaml.org>`_,
it is a "human-friendly data serialization language. It is commonly used for
configuration files and in applications where data is being stored or
transmitted. Two configuration files are required. The first is a
default configuration file, **contour_defaults.yaml**,
which is found in the
*$METPLOTPY_BASE/metplotpy/plots/config* directory.
*$METPLOTPY_BASE* indicates the directory where the METplotpy
source code has been saved.  All default
configuration files are located in the
*$METPLOTPY_BASE/metplotpy/plots/config* directory.
**Default configuration files are automatically loaded by the
plotting code and do not need to be explicitly specified when
generating a plot**.

The second required configuration file is a user-supplied “custom”
configuration file. This  file is used to customize/override the default
settings in the **contour_defaults.yaml** file.

METplus Configuration
=====================

Default Configuration File
__________________________

The following is the *mandatory*, **contour_defaults.yaml**
configuration file, which serves as a starting point for creating a
contour plot,  as it represents the default values set in METviewer.

**NOTE**: This default configuration file is automatically loaded by
**contour.py.**


.. literalinclude:: ../../metplotpy/plots/config/contour_defaults.yaml

Custom Configuration File
_________________________

A second, *mandatory* configuration file is required, which is
used to customize the settings to the contour plot.
The **custom_contour.yaml**  file is included with the
source code and looks like the following:

.. literalinclude:: ../../test/contour/custom_contour.yaml

Copy this custom config file from the directory where the source
code was saved to the working directory:

.. code-block:: ini

  cp $METPLOTPY_BASE/test/contour/custom_contour.yaml $WORKING_DIR/custom_contour.yaml

Modify the *stat_input* setting in the
*$METPLOTPY_BASE/test/contour/custom_contour.yaml*
file to explicitly point to the
*$METPLOTPY_BASE/test/contour*
directory (where the custom config files and sample data reside).
Replace the relative path *./contour.data*
with the full path
*$METPLOTPY_BASE/test/contour/contour.data*
(including replacing *$METPLOTPY_BASE* with the full path to the METplotpy
installation on the system).
Modify the *plot_filename* setting to point to the output path where the
plot will be saved, including the name of the plot.

For example:

*stat_input: /username/myworkspace/METplotpy/test/contour/contour.data*

*plot_filename: /username/working_dir/output_plots/contour_custom.png*

This is where */username/myworkspace/METplotpy* is $METPLOTPY_BASE and
*/username/working_dir* is $WORKING_DIR.  Make sure that the
$WORKING_DIR directory that is specified exists and has the
appropriate read and write permissions. The path listed for
*plot_filename* may be changed to the output directory of one’s choosing.
If this is not set, then the
*plot_filename* setting specified in the
*$METPLOTPY_BASE/metplotpy/plots/config/contour_defaults.yaml*
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


Run from the Command Line
=========================

To generate a contour plot (i.e. using settings in the
**custom_contour.yaml** configuration file),
perform the following:


*  If using the conda environment, verify the conda environment
   is running and has has the required Python packages outlined in the
   `requirements section.
   <https://metplotpy.readthedocs.io/en/latest/Users_Guide/installation-requirements.html>`_

* Set the METPLOTPY_BASE environment variable to point to
  *$METPLOTPY_BASE*.

  For the ksh environment:

  .. code-block:: ini
		
    export METPLOTPY_BASE=$METPLOTPY_BASE

  For the csh environment:

  .. code-block:: ini
		
    setenv METPLOTPY_BASE $METPLOTPY_BASE

  Recall that *$METPLOTPY_BASE* is the directory path indicating where the METplotpy source code was saved.


* Run the following on the command line:

  .. code-block:: ini  

    python $METPLOTPY_BASE/metplotpy/plots/contour/contour.py $WORKING_DIR/custom_contour.yaml

  This will create a PNG file, **contour.png**,
  in the directory that was specified in the *plot_filename*
  setting of the **custom_contour.yaml** config file:

  .. image:: contour.png

* A **contour.png** output file will be created in
  the directory that was  specified in the *plot_filename* config setting
  in the **custom_contour.yaml** config file.
