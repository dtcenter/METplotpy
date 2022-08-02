**********************
FV3 physics tendencies
**********************

Description
===========
Plot mean tendencies of temperature, moisture, and momentum over a time window 
and spatial domain. Tendencies are partitioned into physics parameterizations and 
model dynamics. The residual is defined as the difference between the actual change 
in the state variable and the sum of the physics and dynamics tendencies. One can 
plot a single tendency at multiple pressure levels or plot all tendencies at a 
single pressure level. Plan views (horizontal cross sections) and vertical profiles 
are available. 

Please refer to the `METplus use case documentation
<https://metplus.readthedocs.io/en/develop/generated/model_applications/s2s/UserScript_obsPrecip_obsOnly_Hovmoeller.html#sphx-glr-generated-model-applications-s2s-userscript-obsprecip-obsonly-hovmoeller-py>`_
for instructions on how to plot FV3 physics tendencies.

Required Packages:
==================

* cartopy

* matplotlib

* metpy

* numpy

* pandas

* shapely

* tqdm

* xarray

Required input:
===============

#. FV3 history file with tendencies (fv3_history.nc)

#. FV3 grid specification file with latititude and longitude (grid_spec.nc)



FV3 output and grid specifications. [Grid description in UFS Short Range Weather App user manual](https://ufs-srweather-app.readthedocs.io/en/latest/LAMGrids.html?highlight=grid#limited-area-model-lam-grids-predefined-and-user-generated-options)


Potential tendency variables to read from fv3_history.nc

variables to plot
_________________

The default variable names are shown in the table below and are set in YAML 
config file *$METPLOTPY_BASE/metplotpy/plots/fv3_physics_tend//fv3_physics_tend_defaults.yaml* 

+----------------------------+-------------+-------------------+-------------+-------------+
|           tendency         | temperature | specific humidity |   u-wind    |   v-wind    |
+============================+=============+===================+=============+=============+
|convective gravity wave drag| dt3dt_congwd|                   |du3dt_congwd |dv3dt_congwd |
+----------------------------+-------------+-------------------+-------------+-------------+
|       deep convection      |dt3dt_deepcnv|   dq3dt_deepcnv   |du3dt_deepcnv|dv3dt_deepcnv|
+----------------------------+-------------+-------------------+-------------+-------------+
|     long wave radiation    |  dt3dt_lw   |                   |             |             |
+----------------------------+-------------+-------------------+-------------+-------------+
|        microphysics        |  dt3dt_mp   |     dq3dt_mp      |  du3dt_mp   |   dv3dt_mp  |
+----------------------------+-------------+-------------------+-------------+-------------+
|orographic gravity wave drag| dt3dt_orogwd|                   |du3dt_orogwd |dv3dt_orogwd |
+----------------------------+-------------+-------------------+-------------+-------------+
|  planetary boundary layer  |  dt3dt_pbl  |     dq3dt_pbl     |  du3dt_pbl  |  dv3dt_pbl  |
+----------------------------+-------------+-------------------+-------------+-------------+
|      Rayleigh damping      | dt3dt_rdamp |                   | du3dt_rdamp | dv3dt_rdamp |
+----------------------------+-------------+-------------------+-------------+-------------+
|     shallow convection     |dt3dt_shalcnv|   dq3dt_shalcnv   |du3dt_shalcnv|dv3dt_shalcnv|
+----------------------------+-------------+-------------------+-------------+-------------+
|    short wave radiation    |  dt3dt_sw   |                   |             |             |
+----------------------------+-------------+-------------------+-------------+-------------+
|  total physics (all above) | dt3dt_phys  |     dq3dt_phys    |du3dt_phys   |  dv3dt_phys |
+----------------------------+-------------+-------------------+-------------+-------------+
|           dynamics         | dt3dt_nophys|    dq3dt_nophys   | du3dt_nophys| dv3dt_nophys|
+----------------------------+-------------+-------------------+-------------+-------------+
| state variable at validtime|     tmp     |        spfh       |    ugrd     |    vgrd     |
+----------------------------+-------------+-------------------+-------------+-------------+
| actual change in state var |    dtmp     |       dspfh       |   dugrd     |   dvgrd     |
+----------------------------+-------------+-------------------+-------------+-------------+



Example
=======

Sample Data
___________

The sample data used to create an plot physics tendencies are available in
the `METplus data tar file
<https://dtcenter.ucar.edu/dfiles/code/METplus/METplus_Data/v4.0/sample_data-s2s-4.0.tgz>`_  in the directory
*model_applications/s2s/UserScript_obsPrecip_obsOnly_Hovmoeller*.

Save this file in a directory where you have read and write permissions, such as
$WORKING_DIR/data/fv3_physics_tend, where $WORKING_DIR is the path to the directory where you will save
input data.

Configuration File
___________________

There is a YAML config file located in
*$METPLOTPY_BASE/metplotpy/plots/fv3_physics_tend//fv3_physics_tend_defaults.yaml* 

.. literalinclude:: ../../metplotpy/plots/fv3_physics_tend//fv3_physics_tend_defaults.yaml

*$METPLOTPY_BASE* is the directory where the METplotpy code is saved:

e.g.

*/usr/path/to/METplotpy*  if the source code was cloned or forked from the Github repository

or

*/usr/path/to/METplotpy-x.y.z*  if the source code was downloaded as a zip or gzip'd tar file from the Release link of
the Github repository.  The *x.y.z* is the release number.


Run from the Command Line
=========================

To generate example tendency plots (i.e. using settings in the
**fv3_physics_defaults.yaml** configuration file) perform the following:

*  If using the conda environment, verify the conda environment
   is running and has has the required Python packages specified in the
   **Required Packages** section above.

* Set the METPLOTPY_BASE environment variable to point to
  *$METPLOTPY_BASE*. where $METPLOTPY_BASE is the directory where you saved the
  METplotpy source code (e.g. /home/someuser/METplotpy).

* Run the following on the command line:

Plan view::

   usage: planview_fv3.py [-h] [-d] [--method {nearest,linear,loglinear}] [--ncols NCOLS] [-o OFILE] [-p PFULL [PFULL ...]] [-s SHP] [--subtract SUBTRACT] [-t TWINDOW] [-v VALIDTIME]
                          historyfile gridfile {tmp,spfh,ugrd,vgrd} {nophys,dvgrd,deepcnv,sw,dtmp,rdamp,orogwd,pbl,dspfh,congwd,shalcnv,mp,resid,lw,dugrd}

   Plan view of FV3 diagnostic tendency

   positional arguments:
     historyfile           FV3 history file
     gridfile              FV3 grid spec file
     {tmp,spfh,ugrd,vgrd}  state variable
     {nophys,dvgrd,deepcnv,sw,dtmp,rdamp,orogwd,pbl,dspfh,congwd,shalcnv,mp,resid,lw,dugrd}
                           type of tendency. ignored if pfull is a single level

   optional arguments:
     -h, --help            show this help message and exit
     -d, --debug
     --method {nearest,linear,loglinear}
                           vertical interpolation method (default: nearest)
     --ncols NCOLS         number of columns (default: None)
     -o OFILE, --ofile OFILE
                           name of output image file (default: None)
     -p PFULL [PFULL ...], --pfull PFULL [PFULL ...]
                           pressure level(s) in hPa to plot. If only one pressure level is provided, the type-of-tendency argument will be ignored and all tendencies will be plotted.
                           (default: [1000, 925, 850, 700, 500, 300, 200, 100, 0])
     -s SHP, --shp SHP     shape file directory for mask (default: None)
     --subtract SUBTRACT   FV3 history file to subtract (default: None)
     -t TWINDOW, --twindow TWINDOW
                           time window in hours (default: 3)
     -v VALIDTIME, --validtime VALIDTIME
                           valid time (default: None)

A plot named **tmp_500hPa.20190504_150000-20190504_210000.png** will be generated in the directory from which you ran the plotting command:

.. code-block:: bash

   python planview_fv3.py $WORKING_DIR/fv3_history.nc $WORKING_DIR/grid_spec.nc tmp pbl -p 500 -t 6 -v 20190504T21


.. image:: https://github.com/dtcenter/METplotpy/blob/feature_117_fv3_physics/metplotpy/contributed/fv3_physics_tend/tmp_500hPa.20190504_150000-20190504_210000.png


Vertical profile of areal mean::

   usage: vert_profile_fv3.py [-h] [-d] [-o OFILE] [--resid] [-s SHP]
                              [--subtract SUBTRACT] [-t TWINDOW] [-v VALIDTIME]
                              historyfile gridfile {tmp,spfh,ugrd,vgrd}

   Vertical profile of FV3 diagnostic tendencies

   positional arguments:
     historyfile           FV3 history file
     gridfile              FV3 grid spec file
     {tmp,spfh,ugrd,vgrd}  state variable

   optional arguments:
     -h, --help            show this help message and exit
     -d, --debug
     -o OFILE, --ofile OFILE
                           name of output image file (default: None)
     --resid               calculate residual (default: False)
     -s SHP, --shp SHP     shape file directory for mask (default: None)
     --subtract SUBTRACT   FV3 history file to subtract (default: None)
     -t TWINDOW, --twindow TWINDOW
                           time window in hours (default: 3)
     -v VALIDTIME, --validtime VALIDTIME
                           valid time (default: None)

A plot named **tmp.vert_profile.MID_CONUS.20190504_150000-20190504_210000.png** will be generated in the directory from which you ran the plotting command:

.. code-block:: bash

   python vert_profile_fv3.py $WORKING_DIR/CONUS_25km_GFSv15p2/2019050412/fv3_history.nc $WORKING_DIR/CONUS_25km_GFSv15p2

.. image:: https://github.com/dtcenter/METplotpy/blob/feature_117_fv3_physics/metplotpy/contributed/fv3_physics_tend/tmp.vert_profile.MID_CONUS.20190504_150000-20190504_210000.png


Vertical cross section::

   usage: cross_section_vert.py [-h] [-d] [--dindex DINDEX] [--ncols NCOLS]
                                [-o OFILE] [-s START START] [-e END END]
                                [--subtract SUBTRACT] [-t TWINDOW] [-v VALIDTIME]
                                historyfile gridfile {tmp,spfh,ugrd,vgrd}

   Vertical cross section of FV3 diagnostic tendency

   positional arguments:
     historyfile           FV3 history file
     gridfile              FV3 grid spec file
     {tmp,spfh,ugrd,vgrd}  state variable

   optional arguments:
     -h, --help            show this help message and exit
     -d, --debug
     --dindex DINDEX       tick and gridline interval along cross section
                           (default: 20)
     --ncols NCOLS         number of columns (default: None)
     -o OFILE, --ofile OFILE
                           name of output image file (default: None)
     -s START START, --start START START
                           start point (default: (28, -115))
     -e END END, --end END END
                           end point (default: (30, -82))
     --subtract SUBTRACT   FV3 history file to subtract (default: None)
     -t TWINDOW, --twindow TWINDOW
                           time window in hours (default: 3)
     -v VALIDTIME, --validtime VALIDTIME
                           valid time (default: None)

A plot named **tmp_32.0N-115.0E-34.0N-82.0E.20190504_150000-20190504_210000.png** will be generated in the directory from which you ran the plotting command:

.. code-block:: bash

   python cross_section_vert.py $WORKING_DIR/CONUS_25km_GFSv15p2/2019050412/fv3_history.nc $WORKING_DIR/CONUS_25km_GFSv15p2/2019050412/grid_spec.nc tmp -t 6 -v 20190504T21 -s 32 -115 -e 34 -82

.. image:: https://github.com/dtcenter/METplotpy/blob/feature_117_fv3_physics/metplotpy/contributed/fv3_physics_tend/tmp_32.0N-115.0E-34.0N-82.0E.20190504_150000-20190504_210000.png




Difference plot
_______________


Put file you want to subtract after the --subtract argument:

.. code-block:: bash

   python $METPLOTPY_BASE/metplotpy/plots/fv3_physics_tend/vert_profile_fv3.py $WORKING_DIR/fv3_history.nc $WORKING_DIR/grid_spec.nc tmp --subtract $WORKING_DIR/fv3_history2.nc

where $METPLOTPY_BASE is the directory where you are storing the METplotpy source code and $WORKING_DIR is the
directory where you have read and write permissions and where you are storing all your input data and where you
copied the default config file.


