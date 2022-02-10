# FV3 physics plotting package
Python scripts to plot physics tendencies from FV3 model

## Description
Read tendencies of temperature, moisture, and momentum due to physics parameterizations. Visualize spatial composites of each term over many time snapshots, calculate domain-average vertical profiles over a user-specified region, and plot the residual, which is defined as the difference between the total tendency change and the sum of the physics and non-physics tendencies.

## Python requirements

- argparse
- cartopy
- datetime
- matplotlib.path
- matplotlib.pyplot
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
python fv3_planview.py fv3_history.nc grid_spec.nc tmp nophys
```

## Plot vertical profile

```python
python fv3_vert_profile.py fv3_history.nc grid_spec.nc tmp
```


## Required input

FV3 output and grid specifications. [Grid description in UFS Short Range Weather App user manual](https://ufs-srweather-app.readthedocs.io/en/latest/LAMGrids.html?highlight=grid#limited-area-model-lam-grids-predefined-and-user-generated-options)

- fv3_history.nc
- grid_spec.nc

Potential tendency variables read from fv3_history.nc:

### physics tendencies
- dt3dt_cnvgwd
- dt3dt_deepcnv 
- dt3dt_lw
- dt3dt_mp
- dt3dt_orogwd
- dt3dt_pbl
- dt3dt_rdamp
- dt3dt_shalcnv
- dt3dt_sw

### non-physics tendency
 - dt3dt_nophys

Similar tendency variables for *q* (moisture), *u*, and *v*-wind. 

Potential state variables used to derive cumulative change (final minus initial time) and to compare cumulative change to tendencies:
- tmp
- spfh
- ugrd
- vgrd
