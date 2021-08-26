#export datadir=$HOME/Data/TCRMW
export datadir=/Volumes/d1/minnawin/METcalcpy_Data/Vert_Interp
#export plotdir=$HOME/Plots
export plotdir=/Volumes/d1/minnawin/METplotpy_37_vert_interp/Plots
# export datadir=$DATA_DIR/TCRMW
# export plotdir=$PLOT_DIR
export filename=tc_rmw_dev_test_out.nc
# leave empty if plotting by height (vertical interpolation used)
# or set to True if plotting by pressure level
export by_pressure_lvl=yes

python plot_cross_section.py \
    --datadir=$datadir \
    --plotdir=$plotdir \
    --filename=$filename \
    --by_pressure_lvl=$by_pressure_lvl

#python plot_cross_section.py \
#    --datadir=$datadir \
#    --plotdir=$plotdir \
#    --filename=$filename \
