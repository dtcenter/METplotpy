# ============================*
# ** Copyright UCAR (c) 2020
# ** University Corporation for Atmospheric Research (UCAR)
# ** National Center for Atmospheric Research (NCAR)
# ** Research Applications Lab (RAL)
# ** P.O.Box 3000, Boulder, Colorado, 80307-3000, USA
# ============================*

export datadir=/Users/minnawin/AF_STIG/feature_57_METplotpy_logging/METplotpy/metplotpy/contributed/tc_rmw/Data
export plotdir=/Users/minnawin/AF_STIG/feature_57_METplotpy_logging/METplotpy/metplotpy/contributed/tc_rmw/plots
export filename=vertically_interpolated.nc
export configfile=/Users/minnawin/AF_STIG/feature_57_METplotpy_logging/METplotpy/metplotpy/contributed/tc_rmw/plot_cross_section.yaml
# Default is set to INFO in code, set to any other value here and add to the arguments
# in the call to the plot_cross_section.py below
export loglevel="ERROR"


python plot_cross_section.py \
    --datadir=$datadir \
    --plotdir=$plotdir \
    --filename=$filename \
    --config=$configfile \
#    --loglevel=$loglevel
