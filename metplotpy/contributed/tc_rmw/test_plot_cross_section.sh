# ============================*
# ** Copyright UCAR (c) 2025
# ** University Corporation for Atmospheric Research (UCAR)
# ** National Science Foundation National Center for Atmospheric Research (NSF NCAR)
# ** Research Applications Lab (RAL)
# ** P.O.Box 3000, Boulder, Colorado, 80307-3000, USA
# ============================*
export datadir=/path/to/
export plotdir=/path/to/plot/dir
#export filename=vertically_interpolated.nc
export filename=tc_rmw_vertical_interp.nc
export configfile=/path/to/METplotpy/metplotpy/contributed/tc_rmw/plot_cross_section.yaml

# Default is set to INFO in code, set to any other value here and add to the arguments
# in the call to the plot_cross_section.py below
export loglevel="ERROR"


python plot_cross_section.py \
    --datadir=$datadir \
    --plotdir=$plotdir \
    --filename=$filename \
    --config=$configfile \
#    --loglevel=$loglevel
