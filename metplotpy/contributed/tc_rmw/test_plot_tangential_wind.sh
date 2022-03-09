# ============================*
# ** Copyright UCAR (c) 2022
# ** University Corporation for Atmospheric Research (UCAR)
# ** National Center for Atmospheric Research (NCAR)
# ** Research Applications Lab (RAL)
# ** P.O.Box 3000, Boulder, Colorado, 80307-3000, USA
# ============================*

export input=tc_rmw_example_vertical_interp.nc
export datadir=/path/to/netcdf-input-data
export outputdir=/path/to/output/plots
# name of output file and plot (without file extension)
export output=tangential


python plot_tangential_radial_winds.py \
    --input=$input \
    --datadir=$datadir \
    --outputdir=$outputdir \
    --output=$output

