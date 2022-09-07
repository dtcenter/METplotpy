#!/bin/csh
module load nco

set historyfile=/glade/scratch/mwong/dave/sample_cases/CONUS_25km_GFSv15p2/2019050412/fv3_history.nc

set gridspec=/glade/scratch/mwong/dave/sample_cases/CONUS_25km_GFSv15p2/2019050412/grid_spec.nc

ncks -x -v phalf,refl_10cm,hgtsfc,pressfc,grle,snmr,rwmr,icmr,dzdt,delz,dpres,o3mr,clwmr,zsurf -d time,0,1 $historyfile `basename $historyfile`
ncks -v grid_xt,grid_yt,grid_lont,grid_latt,area $gridspec
