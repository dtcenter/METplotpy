TC-RMW Cross-section Plot
=========================

Description
~~~~~~~~~~~

Generate radial and tangential cross-section plots based on *pressure levels* using output
from the MET TC-RMW tool:

https://met.readthedocs.io/en/latest/Users_Guide/tc-rmw.html

To create the radial and tangential cross-section plots based on *height* (e.g. meters),
use the METcalcpy vertical interpolation module, *vertical_interp.py* to obtain
*vertically interpolated levels*.  Input the MET TC-RMW output into the vertical_interp.py
module to obtain the vertically interpolated levels.  The vertically interpolated output from
the METcalcpy module can then be used as input to the METplotpy cross-section plotting module,
*plot_cross_section.py* to generate the radial and tangential cross-section plots based on height
levels.


Example
~~~~~~~


**Sample Data**

The sample data used to create an example TC-RMW cross-section plot is available in the METplotpy
data tar file:

https://dtcenter.ucar.edu/dfiles/code/METplus/METplotpy/tcrmw/tc_rmw_example.nc.gz


**Configuration Files**

There is an example configuration file:

$METPLOTPY_SOURCE/METplotpy/metplotpy/contributed/tc_rmw/plot_cross_section.yaml

To create a radial and tangential winds cross-section plot after


Run from the Command Line
~~~~~~~~~~~~~~~~~~~~~~~~~

**Height Plots from vertically interpolated data**

**Pressure level Plots**

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
