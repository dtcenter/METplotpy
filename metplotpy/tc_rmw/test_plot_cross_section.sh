# export datadir=$HOME/Data/TCRMW
# export plotdir=$HOME/Plots
export datadir=$DATA_DIR/TCRMW
export plotdir=$PLOT_DIR
export filename=tc_rmw_dev_test_out.nc

python plot_cross_section.py \
    --datadir=$datadir \
    --plotdir=$plotdir \
    --filename=$filename
