# FV3 physics plotting package
Python scripts to plot physics tendencies from FV3 model

## Description
Read tendencies of temperature, moisture, and momentum due to physics parameterizations. Visualize spatial composites of each term over many time snapshots, calculate domain-average vertical profiles over a user-specified region, and plot the residual, which is defined as the difference between the total tendency change and the sum of the physics and non-physics tendencies.

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

## Plot plan view

```python
usage: fv3_planview.py [-h] [-d] [--ncols NCOLS] [-o OFILE]
                       [-p PFULL [PFULL ...]] [-s SHP] [--subtract SUBTRACT]
                       [-t TWINDOW] [-v VALIDTIME]
                       historyfile gridfile {tmp,spfh,ugrd,vgrd}
                       {nophys,congwd,dugrd,lw,resid,shalcnv,sw,dvgrd,rdamp,dspfh,pbl,orogwd,deepcnv,dtmp,mp}

Plan view plot of FV3 diagnostic tendency

positional arguments:
  historyfile           FV3 history file
  gridfile              FV3 grid spec file
  {tmp,spfh,ugrd,vgrd}  state variable
  {nophys,congwd,dugrd,lw,resid,shalcnv,sw,dvgrd,rdamp,dspfh,pbl,orogwd,deepcnv,dtmp,mp}
                        filled contour variable with 2 spatial dims and
                        optional time and vertical dims.

optional arguments:
  -h, --help            show this help message and exit
  -d, --debug
  --ncols NCOLS         number of columns (default: None)
  -o OFILE, --ofile OFILE
                        name of output image file (default: None)
  -p PFULL [PFULL ...], --pfull PFULL [PFULL ...]
                        pressure level(s) in hPa to plot (default: [1000, 925,
                        850, 700, 500, 300, 200, 100, 0])
  -s SHP, --shp SHP     shape file directory for mask (default: None)
  --subtract SUBTRACT   FV3 history file to subtract (default: None)
  -t TWINDOW, --twindow TWINDOW
                        time window in hours (default: 3)
  -v VALIDTIME, --validtime VALIDTIME
                        valid time (default: None)
```

## Plot vertical profile

```python
usage: fv3_vert_profile.py [-h] [-d] [--resid] [-o OFILE] [-s SHP]
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
  --resid               calculate residual (default: False)
  -o OFILE, --ofile OFILE
                        name of output image file (default: None)
  -s SHP, --shp SHP     shape file directory for mask (default: None)
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
|     physics tendencies     | temperature | specific humidity |   u-wind    |   v-wind    |
| -------------------------- | ----------- | ----------------- | ----------- | ----------- |
|convective gravity wave drag| dt3dt_congwd|                   |du3dt_congwd |dv3dt_congwd |
|      deep convection       |dt3dt_deepcnv| dq3dt_deepcnv     |du3dt_deepcnv|dv3dt_deepcnv|
|    long wave radiation     | dt3dt_lw    |                   |             |             |
|      microphysics          | dt3dt_mp    |    dq3dt_mp       |  du3dt_mp   |   dv3dt_mp  |
|orographic gravity wave drag| dt3dt_orogwd|                   |du3dt_orogwd |dv3dt_orogwd |
|   planetary boundary layer | dt3dt_pbl   |  dq3dt_pbl        |du3dt_pbl    |dv3dt_pbl    |
|      Rayleigh damping      | dt3dt_rdamp |                   |du3dt_rdamp  | dv3dt_rdamp |
|     shallow convection     |dt3dt_shalcnv|dq3dt_shalcnv      |du3dt_shalcnv|dv3dt_shalcnv|
|     short wave radiation   |   dt3dt_sw  |                   |             |             |
|     total physics          | dt3dt_phys  | dq3dt_phys        |du3dt_phys   | dv3dt_phys  |
|  *non-physics tendency*    |*dt3dt_nophys*|*dq3dt_nophys*    |*du3dt_nophys*|*dv3dt_nophys* |


State variables used to derive cumulative change (final minus initial time) and to compare cumulative change to tendencies:
|              | temperature | specific humidity | u-wind | v-wind |
| ------------ | ----------- | ----------------- | ------ | ------ |
|state variable|    tmp      |    spfh           | ugrd   | vgrd   |


## Delta Plot

Put file you want to subtract after the --subtract argument.

```python
python fv3_vert_profile.py fv3_history.nc grid_spec.nc tmp --subtract fv3_history2.nc
```
