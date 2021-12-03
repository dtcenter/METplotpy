
export datadir=/path/to/vertically-interpolated-input-data
export plotdir=/path/to/output/plots
export filename=tc_rmw_example_vertical_interp.nc
export configfile=/path/to/configuration-file

python plot_cross_section.py \
    --datadir=$datadir \
    --plotdir=$plotdir \
    --filename=$filename \
    --config=$configfile
