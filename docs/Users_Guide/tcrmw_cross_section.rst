TC-RMW Cross-section Plot
=========================

Description
~~~~~~~~~~~

Generate cross-section plots for TC-RMW data based on *height levels* using output
from the METcalcpy vertical interpolation module, *vertical_interpolation.py*:

https://metcalcpy.readthedocs.io/en/feature_34_vertical_interp/Users_Guide/vertical_interpolation.html


Example
~~~~~~~


**Sample Data**

The sample data used to convert pressure level data to height level is available in the METplotpy
data tar file:

https://dtcenter.ucar.edu/dfiles/code/METplus/METplotpy/tcrmw/tc_rmw_example.nc.gz

Perform the conversion from pressure levels to height levels by following the instructions:

https://metcalcpy.readthedocs.io/en/latest/Users_Guide/vertical_interpolation.html

The output directory you specified in the *height_from_pressure_tcrmw.sh* shell script is where your
tc_rmw_example_vertical_interp.nc file is located.  This output file will be used as input
to the cross section plot, plot_cross_section.py.

**Configuration Files**

An example configuration file (YAML, with .yaml extension) is available as a starting point
for customizing the cross-plot of the height level data:

$METPLOTPY_SOURCE/METplotpy/metplotpy/contributed/tc_rmw/plot_cross_section.yaml

.. literalinclude:: ../../metplotpy/contributed/tc_rmw/plot_cross_section.yaml

where $METPLOTPY_SOURCE is the location where you saved the METplotpy source code.



Run from the Command Line
~~~~~~~~~~~~~~~~~~~~~~~~~


You can generate cross-section plots for any variable in the input data (i.e. the output from
METcalcpy vertical_interp.py) using the *test_plot_cross_section.sh* Bourne shell script:

.. literalinclude:: ../../metplotpy/contributed/tc_rmw/test_plot_cross_section.sh

Set up the *datadir*, *plotdir*, *filename*, and *configfile* values in the *test_plot_cross_section.sh* script to
point to the appropriate locations:

*datadir* is the location of the input netCDF file (the directory where you saved the
output from the METcalcpy vertical interpolation)

*plotdir* is the location of the output plot

*filename* is the name of the input netCDF file (the

*configfile* is the YAML config file that is used to set plot customizations (line colors, labels, etc.)

Required Packages:
~~~~~~~~~~~~~~~~~~

Specific version numbers are specified when necessary.  If versions are not specified, use a
compatible version number for your operating system and existing packages.

**Python 3.7** or above

METcalcpy 1.1.0

matplotlib 3.4.3

metpy 1.1.0

netcdf4 1.5.7 or above

numpy

pandas

pint 0.17

xarray

yaml
