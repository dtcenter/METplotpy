
export datadir=/Volumes/d1/minnawin/METcalcpy_Data/Vert_Interp

export plotdir=/Volumes/d1/minnawin/METplotpy_37_vert_interp/Plots

export filename=tc_rmw_dev_test_out.nc

export configfile=/Volumes/d1/minnawin/METplotpy_37_vert_interp/METplotpy/metplotpy/contributed/tc_rmw/plot_cross_section.yaml

python plot_cross_section.py \
    --datadir=$datadir \
    --plotdir=$plotdir \
    --filename=$filename \
    --config=$configfile

#python plot_cross_section.py \
#    --datadir=$datadir \
#    --plotdir=$plotdir \
#    --filename=$filename \
