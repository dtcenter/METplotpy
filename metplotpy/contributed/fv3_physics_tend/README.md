# FV3 physics plotting package
Python scripts to plot physics tendencies from FV3 model

## Required Python modules

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

## Description
Read tendencies of temperature, moisture, and momentum due to physics parameterizations. Visualize spatial composites of each term over many time snapshots, calculate domain-average vertical profiles over a user-specified region, and plot the residual, which is defined as the difference between the total tendency change and the sum of the physics and non-physics tendencies.

## Input

FV3 output and grid specifications. [Grid description in UFS Short Range Weather App user manual](https://ufs-srweather-app.readthedocs.io/en/latest/LAMGrids.html?highlight=grid#limited-area-model-lam-grids-predefined-and-user-generated-options)

- fv3_history.nc
- grid_spec.nc

Variables read from fv3_history.nc:

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

Final temperature to derive cumulative change (difference between t = 12 and t = 1, where t is the output timestep) and compare to tendencies
- tmp

### non-physics tendency
 - dt3dt_nophys

Similar variables for *q* (moisture), *u*, and *v*-wind.

## How to use

## Output
