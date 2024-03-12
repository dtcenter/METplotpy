***********
TCMPR Plots
***********

Description
===========

The TCMPR plots were originally available under the MET repository: https://github.com/dtcenter/MET
and written in R script.  The code has been rewritten in Python and is located in the METplotpy repository:
https://github.com/dtcenter/METplotpy/metplotpy/plots/tcmpr_plots


There are numerous TCMPR plots that can be generated within **one** YAML configuration files:

  * mean line plot
  * median line plot
  * boxplot
  * relative performance plot
  * rank plot
  * mean skill line plot
  * median skill line plot

Generating multiple plots within a single configuration file reduces the number of command line
commands to generate the plots.

However, when more specific titles and plot customizations are desired for particular plot types,
each plot type can be defined with a corresponding configuration file
(e.g. a box plot will have a config file specifying settings specific to the
boxplot, a reliability plot will have a corresponding config file with settings relevant to a reliability plot, etc.).

Example
=======

Sample Data
-----------

The data is text output from MET in columnar format. The sample data used to
create various TCMPR plots is available in the
`METplotpy <https://github.com/dtcenter/METplotpy>`_ repository, where the TCMPR plot tests are located:

*$METPLOTPY_BASE/metplotpy/test/tcmpr_plots/Data*

*$METPLOTPY_BASE* is the directory where the METplotpy code is saved:

e.g.

*/usr/path/to/METplotpy*  if the source code was cloned or forked from the Github repository

or

*/usr/path/to/METplotpy-x.y.z*  if the source code was downloaded as a zip or gzip'd tar file from the Release link of
the Github repository.  The *x.y.z* is the release number.


Configuration Files
-------------------

The TCMPR plots utilize *two* YAML configuration files to indicate where input
data is located and to set plot attributes.

YAML is a recursive acronym for "YAML Ain't Markup Language" and according to
`yaml.org <https://yaml.org>`_, it is a
"human-friendly data serialization language".
It is commonly used for configuration files and in applications where
data is being stored or transmitted.

A **mandatory default configuration** file specifies line/series colors, symbol shapes, symbol sizes,
margins, log levels, x- and y-label settings that can be used by numerous plot types. These default values
can be overridden by the custom configuration file.

A **mandatory custom configuration file is also required**. Multiple plot types can be requested
in **one** configuration file (resulting in a single call to tcmpr.py to generate all the specified plots).
In this case, the TCMPR plotting scripts can create the title and  x- and y-axis
labels based on the plot type and requested statistics specified in the config file.

If particular plot types require specific/custom titles and/or
x- and y-axis labels, then each plot type can have a corresponding configuration file with values specific to this plot
type, statistics of interest (e.g. ABS(AMSLP-BMSLP), TK_ERR, etc.), fixed variables
(e.g. BASIN:AL, LEVEL:[SS, HU, TS]), and series (e.g. AMODEL:[H221, M221]).

.. note::

  The YAML configuration files **do not support expanding environment variables**.
  If you see an environment variable referenced in this documentation for a YAML configuration item,
  please be aware the **full value of that environment variable must be used**.

METplus Configuration
=====================

Default Configuration File
--------------------------

A default configuration file, tcmpr_defaults.yaml has some default settings for three lines/series such as plot
size, margins, etc. that don't require modification.  There are some example colors and line and symbol styles and
sizes for three lines/series.  The default logging level is set to ERROR, the least verbose.  Any of these
settings can be overridden by setting new values in the custom configuration file(s).

.. literalinclude:: ../../metplotpy/plots/config/tcmpr_defaults.yaml

**NOTE**: This default configuration file is automatically loaded by
**tcmpr.py** and **does not require any modifications**.

In the default config file, logging is set to stdout and the log level is ERROR (i.e. any log messages
of type ERROR will be logged).  If the log_filename and log_level are
not specified in the custom configuration file, these settings will be used.


Custom Configuration File
-------------------------

A second, *mandatory* configuration file is required, which is
used to customize the settings to the specified TCMPR plot type(s). The **tcmpr_multi_plots.yaml**
file is included with the source code.  The settings in this custom configuration file override those in the
default config file.

Copy this custom config file from the directory where the source code was
saved to the working directory:

.. code-block:: ini
		
  cp $METPLOTPY_BASE/test/tcmpr_plots/tcmpr_multi_plots.yaml $WORKING_DIR/tcmpr_multi_plots.yaml

Specify the input data in one of two ways:

* Specify by directory (use all files under this directory):

    tcst_dir: '/path/to/tcmpr_sample_data'

    Replace the */path/to* with the full path to the sample data

* Specify by list of .tcst files:

    tcst_files: ['a.tcst', 'b.tcst', 'w.tcst', 'z.tcst' ]

Specify the series/line values of interest:

* series_val_1:
  AMODEL:
    - H221
    - M221

  specify a key (AMODEL) and a list of one or more values of interest (e.g. the H221 and M221 models)

Specify the independent (x-axis) variable,  values and labels:

* indy_var: 'LEAD'

* indy_vals:
     - 0
     - 6
     - 12
     - 18

* indy_labels:
    - '00'
    - '06'
    - '12'
    - '18'

The example above is requesting the forecast lead times ('LEAD' for the example data set provided) for 0, 6, 12, and 18
hours with the corresponding labels (surrounded by either single or double quotes).  The indy_var is set to 'LEAD' in
the tcmpr_defaults.yaml config file.  Override this to the name of the forecast lead column in the input
data.


Specify the criteria for subsetting the input data:

* fixed_vars_vals_input:
  BASIN:
    - AL
  LEVEL:
    - SS
    - SD
    - TS
    - TD
    - HU


In the example above, the data to be considered should correspond to the Atlantic Basin and the five specified levels.

Modify the *tcst_dir* setting in the
*$WORKING_DIR/tcmpr_multi_plots.yaml* file to
explicitly point to the *$METPLOTPY_BASE/test/tcmpr_plots/Data*
directory to use the sample data.
Replace the */path/to/tcmpr_sample_data* with the full path
*$METPLOTPY/test/tcmpr_plots/Data*
(including replacing *$METPLOTPY_BASE* with the full path to the METplotpy
installation on the system).  Modify the *tcst_dir*
setting to point to the output path where the plot will be saved.


For example:

*tcst_dir: /username/myworkspace/METplotpy/test/tcmpr_plots/Data*

*prefix: /prefix_applied_to_all_plot_names*

The */username/myworkspace/METplotpy* corresponds to *$METPLOTPY_BASE* and
*/username/working_dir* corresponds to *$WORKING_DIR*.  Make sure that the
*$WORKING_DIR* directory that is specified exists and has the appropriate
read and write permissions.  The prefix specified for *plot_filename* may be
changed to the output directory of one's choosing.  If this is not set,
then the *plot_filename* setting specified in the
*$METPLOTPY_BASE/metplotpy/plots/config/line_defaults.yaml*
configuration file will be used.

To save the intermediate **.points1** file (used by METviewer and is useful
for debugging but not required), set the *dump_points_1*
setting to True. Uncomment or add (if it doesn't exist) the
*points_path* setting.

*dump_points_1: 'True'*

*points_path: '/dir_to_save_points1_file'*

Replace the */dir_to_save_points1_file* to the same directory where
the **.points1** file is saved.
If *points_path* is commented out (indicated by a '#' symbol in front of it),
remove the '#' symbol to uncomment the points_path so that it will be
used by the code.  Make sure that this directory exists and has the
appropriate read and write permissions.  **NOTE**: the *points_path* setting
is **optional** and does not need to be defined in the configuration file
unless saving the intermediate **.points1** file is desired.

To save the log output to a file, uncomment the *log_filename* entry and specify the path and
name of the log file.  Select a directory with the appropriate read and write
privileges.  To modify the verbosity of logging than what is set in the default config
file, uncomment the *log_level* entry and specify the log level  (debug and info are higher verbosity, warning and error
are lower verbosity).


Generate seven different plot types in one configuration file:
-------------------------------------------------------------

To use the *default* settings defined in the **line_defaults.yaml**
file, specify a minimal custom configuration file (**minimal_line.yaml**),
which consists of only a comment block, but can be any empty file
(if the user has write permissions for the output filename path corresponding
to the *plot_filename* setting in the default configuration file.
Otherwise the user  will need to specify a *plot_filename* in the
**minimal_line.yaml** file):

.. literalinclude:: ../../test/line/minimal_line.yaml


Copy this file to the working directory:

.. code-block:: ini

  cp $METPLOTPY_BASE/test/line/minimal_line.yaml $WORKING_DIR/minimal_line.yaml


Add the *stat_input* (input data) and *plot_filename* (output file/plot path)
settings to the **$WORKING_DIR/minimal_line.yaml**
file (anywhere below the comment block). The *stat_input* setting
explicitly indicates where the sample data and custom configuration
files are located.  Set the *stat_input* to
*$METPLOTPY_BASE/test/line/line.data* and set the
*plot_filename* to *$WORKING_DIR/output_plots/line_default.png* (making sure to
replace environment variables with their actual values):

*stat_input: $METPLOTPY_BASE/test/line/line.data*

*plot_filename: $WORKING_DIR/output_plots/line_default.png*

*$WORKING_DIR* is the working directory where all the custom
configuration files are being saved. **NOTE**: If the *plot_filename*
(output directory) is specified to a directory other than the
*$WORKING_DIR/output_plots*, the user must have read and write permissions
to that directory.

**NOTE**: This default plot does not display any of the data points.
It is to be used as a template for setting up margins, captions,
label sizes, etc.

Run from the Command Line
=========================

The **tcmpr_multi_plots.yaml** configuration file, in combination with the
**tcmpr_defaults.yaml** configuration file, generates the following plots:
    *

.. image:: figure/line.png

To generate the seven plot types using the **tcmpr_defaults.yaml** and
**tcmpr_multi_plots.yaml** config files, perform the following:

* If using the conda environment, verify the conda environment
  is running and has the required
  `Python packages
  <https://metplotpy.readthedocs.io/en/latest/Users_Guide/installation.html#python-requirements>`_
  outlined in the requirements section.

* Set the METPLOTPY_BASE environment variable to point to
  *$METPLOTPY_BASE*.

  For the ksh environment:

  .. code-block:: ini
		
    export METPLOTPY_BASE=$METPLOTPY_BASE

  For the csh environment:

  .. code-block:: ini

    setenv METPLOTPY_BASE $METPLOTPY_BASE

  Recall that *$METPLOTPY_BASE* is the directory path indicating where the METplotpy source code was saved.

  To generate the above **"custom"** plot (i.e using some custom
  configuration settings), use the custom configuration file,
  **custom_line.yaml**.

* Enter the following command:
  
  .. code-block:: ini

    python $METPLOTPY_BASE/metplotpy/plots/tcmpr_plots/tcmpr.py $WORKING_DIR/tcmpr_multi_plots.yaml


* Fourteen different output files will be created in the directory specified in
  the *plot_dir* configuration setting in the **tcmpr_multi_plots.yaml** config file.



* A **line_default.png** output file will be created in the
  directory specified in the *plot_filename* configuration setting
  in the **line_defaults.yaml** config file.

  .. image:: figure/line_default.png

  **NOTE**: This default plot does not display any of the data points.
  It is to be used as a template for
  setting up margins, captions, label sizes, etc.
