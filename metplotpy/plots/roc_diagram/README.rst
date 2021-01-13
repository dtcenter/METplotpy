**ROC Diagrams README**

This file describes the information necessary for generating ROC diagrams,
which are implemented in Python Plotly.  The user must supply a custom YAML
configuration file that contains settings that supersede the values in the default
config file, performance_diagram_defaults.yaml.  This can be an empty file, if the user
wishes to use the default settings as defined in the roc_diagram_defaults.yaml config file.

The default configuration file uses example data that is output from the MET tool.


**Requirements**

It is recommended that you run within a conda environment
with the following packages installed:

Python 3.6.3

psutils 5.7.2

python-kaleido 0.0.3

Cartopy 0.17.0 or above

pandas 1.1.0

numpy 1.19.1

scipy 1.5.0

plotly 4.9.0

matplotlib 3.3.1 or above

netcdf4 1.4.1

pyyaml 5.3.1

metcalcpy 0.0.1 or above

METcalcpy:
Clone the METcalcpy repository from https://github.com/dtcenter/METcalcpy


**Set PYTHONPATH env to use METcalcpy modules**

Clone the METcalcpy repository

Include the path to the METcalcpy in your PYTHONPATH environment

e.g. if your path to METcalcpy is /home/username/METcalcpy

set up your PYTHONPATH this way:

*csh*:


setenv PYTHONPATH /home/username/METcalcpy/metcalcpy:/home/username/METcalcpy/metcalcpy/util


*bash*:


export PYTHONPATH=/home/username/METcalcpy/metcalcpy:/home/username/METcalcpy/metcalcpy/util



**How to Run**

Append the following to your *PYTHONPATH*:

$METPLOTPY_SOURCE/METplotpy/metplotpy/plots/roc_diagram:$METPLOTPY_SOURCE/METplotpy/metplotpy/plots:$METPLOTPY_SOURCE/METplotpy/metplotpy/


where $METPLOTPY_SOURCE is the path to where you downloaded/cloned the METplotpy code.


e.g.

*csh*:

setenv PYTHONPATH ${PYTHONPATH}:$METPLOTPY_SOURCE/METplotpy

*bash*:

export PYTHONPATH ${PYTHONPATH}:$METPLOTPY_SOURCE/METplotpy

There is one sample data file (plot_20200507_074426.data) and one sample custom config file,
custom_performance_diagram.yaml that are available in the directory
where the performance_diagram.py file resides.


**To generate a plot using only the default settings (these are defined in the
METplotpy/metplotpy/plots/config/roc_diagram_defaults.yaml configuration
file)**

From the command line, run:

*python performance_diagram.py ./minimal_roc_diagram.yaml*


A plot named roc_diagram_minimal.png will be created in the
$METPLOTPY_SOURCE/METplotpy/metplotpy/plots/roc_diagram directory.
A plot_20200507_074426.points1 text file is also created, which has the pofd and pody
values that were plotted.  Finally, a .html file is created which is used by METviewer
to make the plot interactive within the METviewer tool.

**To generate a plot that overrides some of the default settings with some of the settings in the custom config file
(custom_roc_diagram.yaml)**

From the command line, run:

*python performance_diagram.py ./custom_roc_diagram.yaml*

This uses the input data file plot_20200507_74426.data that is included
in the source.  A ROC diagram, named roc_diagram_default.png
is created, along with the plot_202005_074426.points1 file.  The latter file
contains the POFD and PODY points that are plotted.  A .html file is created
which is used by METviewer
to make the plot interactive within the METviewer tool.

**Description of Configuration settings**

The performance diagram relies on two configuration files:
a default and a custom file that can override
settings defined in the default:

* roc_diagram_defaults.yaml

* custom_roc_diagram.yaml

The default config files for all plot types are located in the *METplotpy/metplotpy/config
directory*.

The custom config files reside in the directory corresponding to that plot type, ie the
custom_roc_diagram.yaml file is located in the *$METPLOT_SOURCE/METplotpy/metplotpy/plots/roc_diagram*
directory.

The settings in the configuration file are used by METviewer to generate
plots within that application.

For a ROC diagram, the following settings are used (there are some settings that
are not used for generating a ROC diagram, but are required by METviewer).

Required settings:

- title

  The title of the plot.  If no title is desired, set this to an empty string: ' '



- title_offset

  The left-right positioning of the title

- title_size

  Font size in terms of a multiplier (applied to an internal font size)

- title_weight

  setting values:

    1=plain text

    2=bold

    3=italic

    4=bold italic

- plot_width

  Sets the width of the output plot

- plot_height

  Sets the height of the output plot

- plot_res

  The plot resolution, a higher value requests higher resolution image

- plot_units

  in for units in inches

  cm for units in centimeters

- roc_pct

   Calculate ROC points using the probabilistic contingency table (PCT)

   set to False if roc_ctc is True

   set to True if roc_ctc if False

- roc_ctc

   Calculate ROC points using the  contingency table counts (CTC)

   set to True if roc_pct is False

   set to False if roc_pct if True

- add_point_thresholds

  True  plots the threshold value for each point

  False  do not plot the threshold value

- user_legend

  empty string ('') or legend text you wish to display

- legend_box

 ``n    for none/no box around the legend``

 ``o    for a box around the legend``

- legend_inset

  ``x     A float value indicating the x-position of legend``

  ``y     A float value indicating the y-position of the legend``

- legend_size

  A float value that is a scaling factor to be applied to some default legend size.

  A number greater than 1.0 will increase the legend size; a value less than 1.0 will

  result in a smaller legend


- plot_disp

 True if you want your plot to be displayed

 False otherwise

- series_order

    For multiple series, indicate the order in which you want your series plotted:

    ``- 3   (first series to be plotted third)``

    ``- 1   (second series to be plotted first)``

    ``- 2   (third series to be plotted second)``

    This enables you to easily modify the order of how things are plotted (using their
    corresponding settings)

- stat_curve

 set to 'None'  - for ROC diagram, no stat curves are currently supported


- series_symbols

  Supported values:

   ``"small circle"   an open circle``

   ``"circle"         a circle``

   ``"square"         a square``

   ``"rhombus"        a diamond``

   ``"ring"           a hexagon``

   ``"triangle"       an upside-down triangle``

- plot_caption

  Set to empty string if no caption is desired

- caption_size

  Float value, values larger than one will create caption larger than the default size

  Values less than one will create a caption smaller than the default size.

- caption_offset

  The up-down offset of the caption relative to the x-axis

- caption_align

  The left-right alignment of the caption

- xaxis

  Label to apply to the x-axis

- xlab_offset

 The up-down offset of the x-axis label

- xlab_size

  Size of the x-axis label

- xtlab_size

 The size of the tick labels for the x-axis

- yaxis_1

  The label for the y-axis.  Set to empty string if no label is desired.

- yaxis_2
  The label for the second y-axis.  Set to empty string for this plot type.

- ylab_offset

  The up-down offset of the y-axis label

- ytlab_size

  The size of the tick labels for the y-axis

- stat_input

 The full file path and filename for the input data needed to generate this plot

- plot_filename

  The full file path and name for the plot that will be generated.  Currently, only
  png files will be generated.



















