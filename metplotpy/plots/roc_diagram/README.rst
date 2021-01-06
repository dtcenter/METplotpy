**ROC Diagrams README**

This file describes the information necessary for generating ROC diagrams,
which are implemented in Python Plotly.  The user must supply a custom YAML
configuration file that contains settings that supersede the values in the default
config file, performance_diagram_defaults.yaml.

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

netcdf4 1.4.1

pyyaml 5.3.1

metcalcpy 0.0.1 or above

METcalcpy:
Clone the METcalcpy repository from https://github.com/dtcenter/METcalcpy

**How to install METcalcpy in your conda env**

From within your active conda environment, cd to the METcalcpy/ directory, you should see the setup.py script

From this directory, run *pip install -e .*

The *-e* option allows this installation to be editable, which is useful in that you can update your METcalcpy/metcalcpy
source code without reinstalling


**Alternative to installing METcalcpy (set PYTHONPATH environment)**

Clone the METcalcpy repository

Include the METcalcpy path in your PYTHONPATH environment

e.g. if your path to METcalcpy is /home/username/METcalcpy

set up your PYTHONPATH this way:

*csh*:


setenv PYTHONPATH /home/username/METcalcpy/metcalcpy


*bash*:


export PYTHONPATH=/home/username/METcalcpy/metcalcpy



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

From the command line, run:

*python performance_diagram.py ./custom_roc_diagram.yaml*

This uses the input data file plot_20200507_74426.data that is included
in the source.  A performance diagram, named performance_diagram_default.png
is created, along with a plot_202005_74426.points1 file.  The latter file
contains the POFD and PODY points that are plotted.

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

   set to True if roc_ctc is False

   set to False if roc_ctc if True

- add_point_thresholds

  True  plots the threshold value for each point

  False do not plot the threshold value

- user_legend


















