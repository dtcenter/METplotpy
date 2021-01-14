**Performance Diagram README**

This file describes the information necessary for generating performance diagrams,
which are implemented in Matplotlib.  The user must supply a custom YAML
configuration file that contains settings that supersede the values in the default
config file, performance_diagram_defaults.yaml.

The default configuration file uses example data that is output from the MET tool.  


**Requirements**

It is recommended that you run within a conda environment
with the following packages installed:

Python 3.6.3

Matplotlib 3.3.1

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


**How to Run**

Set your *PYTHONPATH* to the following:

$METPLOTPY_SOURCE/METplotpy/metplotpy:$METPLOTPY_SOURCE/METplotpy/metplotpy/plots:$METPLOTPY_SOURCE/METplotpy/metplotpy/plots/performance_diagram


where $METPLOTPY_SOURCE is the path to where you downloaded/cloned the METplotpy code.


There is one sample data file (plot_20200317_151252.data), one sample custom config file
(custom_performance_diagram.yaml) and one minimal custom config file
(minimal_performance_diagram.yaml) that are available in the directory
where the performance_diagram.py file resides.

From the command line, run:

*python performance_diagram.py ./minimal_performance_diagram.yaml*

This uses the input data file plot_20200317_151252.data that is included
in the source.  A performance diagram, named performance_diagram_m.png
is created, along with a plot_20200317_151252.points1 file.  The latter file
contains the (1-FAR) and PODY points that are plotted. A plot named
performance_diagram_default.png is generated.

*python performance_diagram.py ./custom_performance_diagram.yaml*

This uses the input data file plot_20200317_151252.data that is included
in the source.  A performance diagram, named performance_diagram_default.png
is created, along with a plot_20200317_151252.points1 file.  The latter file
contains the (1-FAR) and PODY points that are plotted.
