export datadir=$HOME/Data/TCRMW
export plotdir=$HOME/Plots
export trackfile=tc_rmw_out.nc
export scalar_field=PRMSL

python plot_fields.py \
    --datadir=$datadir \
    --plotdir=$plotdir \
    --trackfile=$trackfile \
    --scalar_field=$scalar_field
