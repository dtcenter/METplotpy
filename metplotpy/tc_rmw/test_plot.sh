export datadir=$HOME/Data/TCRMW
export plotdir=$HOME/Plots
export trackfile=tc_rmw_out.nc
export scalar_field=PRMSL
export level=L0
export step=3

python plot_fields.py \
    --datadir=$datadir \
    --plotdir=$plotdir \
    --trackfile=$trackfile \
    --scalar_field=$scalar_field \
    --level=$level \
    --step=$step
