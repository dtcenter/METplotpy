
# ============================*
# ** Copyright UCAR (c) 2020
# ** University Corporation for Atmospheric Research (UCAR)
# ** National Center for Atmospheric Research (NCAR)
# ** Research Applications Lab (RAL)
# ** P.O.Box 3000, Boulder, Colorado, 80307-3000, USA
# ============================*



export datadir=$HOME/Data/TCRMW
export plotdir=$HOME/Plots
export trackfile=tc_rmw_last_test_out.nc
export scalar_field=PRMSL
export level=L0
export start=2
export step=3

python plot_fields.py \
    --datadir=$datadir \
    --plotdir=$plotdir \
    --trackfile=$trackfile \
    --scalar_field=$scalar_field \
    --level=$level \
    --step=$step \
    --start=$start \
    --title='FV3GFS Hurrican Matthew 2016 Oct 5 03:00Z'
