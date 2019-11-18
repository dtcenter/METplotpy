export datadir=$HOME/Data/TCRMW
export plotdir=$HOME/Plots
export filename=tc_rmw_dev_test_out.nc

python plot_cross_section.py \
    --datadir=$datadir \
    --filename=$filename
