# ============================*
# ** Copyright UCAR (c) 2020
# ** University Corporation for Atmospheric Research (UCAR)
# ** National Center for Atmospheric Research (NCAR)
# ** Research Applications Lab (RAL)
# ** P.O.Box 3000, Boulder, Colorado, 80307-3000, USA
# ============================*

export datadir=/path/to/vertically-interpolated-input-data
export plotdir=/path/to/output/plots
export filename=tc_rmw_example_vertical_interp.nc
export configfile=/path/to/configuration-file

python plot_cross_section.py \
    --datadir=$datadir \
    --plotdir=$plotdir \
    --filename=$filename \
    --config=$configfile
