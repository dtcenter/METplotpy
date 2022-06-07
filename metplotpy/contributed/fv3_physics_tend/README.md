# FV3 physics plotting package
Python scripts to plot physics tendencies from FV3 model

## Description
Calculate mean tendencies of temperature, moisture, and momentum over a time window and spatial domain. Tendencies are partitioned into physics parameterizations and model dynamics. The residual is defined as the difference between the actual change in the state variable and the sum of the physics and dynamics tendencies. One can plot a single tendency at multiple pressure levels or plot all tendencies at a single pressure level. Plan views (horizontal cross sections) and vertical profiles are available. 

## Python requirements

- argparse
- cartopy
- datetime
- logging
- matplotlib.path
- matplotlib.pyplot
- matplotlib.ticker
- metpy.units
- numpy
- os
- pandas
- shapely.geometry
- sys
- xarray

## Installation

On NCAR's casper:
```csh
module reset
module load conda
conda deactivate
conda activate npl-2202

```

Then install METplotpy into your conda environment as described in [METplotpy installation instructions](https://github.com/dtcenter/METplotpy/blob/main_v1.0/docs/Users_Guide/installation.rst#install-metcalcpy-in-your-conda-environment)

## Plan view

```
usage: planview_fv3.py [-h] [-d] [--ncols NCOLS] [-o OFILE]
                       [-p PFULL [PFULL ...]] [-s SHP] [--subtract SUBTRACT]
                       [-t TWINDOW] [-v VALIDTIME]
                       historyfile gridfile {tmp,spfh,ugrd,vgrd}
                       {orogwd,dspfh,shalcnv,resid,pbl,rdamp,lw,nophys,dvgrd,dtmp,sw,dugrd,deepcnv,mp,congwd}

Plan view of FV3 diagnostic tendency

positional arguments:
  historyfile           FV3 history file
  gridfile              FV3 grid spec file
  {tmp,spfh,ugrd,vgrd}  state variable
  {orogwd,dspfh,shalcnv,resid,pbl,rdamp,lw,nophys,dvgrd,dtmp,sw,dugrd,deepcnv,mp,congwd}
                        type of tendency. ignored if pfull is a single level

optional arguments:
  -h, --help            show this help message and exit
  -d, --debug
  --ncols NCOLS         number of columns (default: None)
  -o OFILE, --ofile OFILE
                        name of output image file (default: None)
  -p PFULL [PFULL ...], --pfull PFULL [PFULL ...]
                        pressure level(s) in hPa to plot. If only one pressure
                        level is provided, the type-of-tendency argument will
                        be ignored and all tendencies will be plotted.
                        (default: [1000, 925, 850, 700, 500, 300, 200, 100,
                        0])
  -s SHP, --shp SHP     shape file directory for mask (default: None)
  --subtract SUBTRACT   FV3 history file to subtract (default: None)
  -t TWINDOW, --twindow TWINDOW
                        time window in hours (default: 3)
  -v VALIDTIME, --validtime VALIDTIME
                        valid time (default: None)
```

## Vertical profile of areal mean

```
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
```

## Vertical cross section 
```
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
```


## Required input

FV3 output and grid specifications. [Grid description in UFS Short Range Weather App user manual](https://ufs-srweather-app.readthedocs.io/en/latest/LAMGrids.html?highlight=grid#limited-area-model-lam-grids-predefined-and-user-generated-options)

- fv3_history.nc
- grid_spec.nc

Potential tendency variables to read from fv3_history.nc:

### variables to plot
|           tendency         | temperature | specific humidity |   u-wind    |   v-wind    |
| -------------------------- | ----------- | ----------------- | ----------- | ----------- |
|convective gravity wave drag| dt3dt_congwd|                   |du3dt_congwd |dv3dt_congwd |
|       deep convection      |dt3dt_deepcnv|   dq3dt_deepcnv   |du3dt_deepcnv|dv3dt_deepcnv|
|     long wave radiation    |  dt3dt_lw   |                   |             |             |
|        microphysics        |  dt3dt_mp   |     dq3dt_mp      |  du3dt_mp   |   dv3dt_mp  |
|orographic gravity wave drag| dt3dt_orogwd|                   |du3dt_orogwd |dv3dt_orogwd |
|  planetary boundary layer  |  dt3dt_pbl  |     dq3dt_pbl     |  du3dt_pbl  |  dv3dt_pbl  |
|      Rayleigh damping      | dt3dt_rdamp |                   | du3dt_rdamp | dv3dt_rdamp |
|     shallow convection     |dt3dt_shalcnv|   dq3dt_shalcnv   |du3dt_shalcnv|dv3dt_shalcnv|
|    short wave radiation    |  dt3dt_sw   |                   |             |             |
|    total physics (above)   | dt3dt_phys  |     dq3dt_phys    |du3dt_phys   |  dv3dt_phys |
|           dynamics         | dt3dt_nophys|    dq3dt_nophys   | du3dt_nophys| dv3dt_nophys|
| -------------------------- | ----------- | ----------------- | ----------- | ----------- |
| state variable at validtime|     tmp     |        spfh       |    ugrd     |    vgrd     |
| actual change in state var |    dtmp     |       dspfh       |   dugrd     |   dvgrd     |


## Difference plot

Put file you want to subtract after the --subtract argument.

```python
python fv3_vert_profile.py fv3_history.nc grid_spec.nc tmp --subtract fv3_history2.nc
```
