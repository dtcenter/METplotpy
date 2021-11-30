TC-RMW Cross-section Plot
=========================

Description
~~~~~~~~~~~


Example
~~~~~~~


**Sample Data**



**Configuration Files**

There is an example configuration file:

$METPLOTPY_SOURCE/METplotpy/metplotpy/contributed/tc_rmw/plot_cross_section.yaml


Run from the Command Line
~~~~~~~~~~~~~~~~~~~~~~~~~

You can generate radial and cross-section plots for input data using the *test_plot_cross_section.sh*
Bourne shell script.

Set up the *datadir*, *plotdir*, *filename*, and *configfile* values in the *test_plot_cross_section.sh* script to
point to the appropriate locations.
The *datadir* is the location of the input netCDF file, the *plotdir* is the location of the
output plot, the *filename* is the name of the input netCDF file, and the *configfile* is the
YAML config file (an example is in the $METPLOTPY_SOURCE/METplotpy/metplotpy/contributed/tc_rmw
directory).

Required Packages:
~~~~~~~~~~~~~~~~~~

Specific version numbers are specified when necessary.  If not specified, find any
compatible version numbers for your operating system.

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
