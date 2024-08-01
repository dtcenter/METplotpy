#!/bin/csh
module load nco

set historyfile=/glade/scratch/mwong/dave/sample_cases/CONUS_25km_GFSv15p2/2019050412/fv3_history.nc
set historyfile=/glade/campaign/mmm/parc/ahijevyc/METplotpy/DavidA_fv3_history_etc_files/fv3_history.nc

set gridspec=/glade/scratch/mwong/dave/sample_cases/CONUS_25km_GFSv15p2/2019050412/grid_spec.nc
set gridspec=/glade/campaign/mmm/parc/ahijevyc/METplotpy/DavidA_fv3_history_etc_files/grid_spec.nc

# extract variables 
ncks -v pfull,time,spfh,dtend_qv_pbl,dtend_qv_deepcnv,dtend_qv_shalcnv,dtend_qv_mp,dtend_qv_phys,dtend_qv_nophys,tmp,dtend_temp_lw,dtend_temp_sw,dtend_temp_pbl,dtend_temp_deepcnv,dtend_temp_shalcnv,dtend_temp_mp,dtend_temp_orogwd,dtend_temp_cnvgwd,dtend_temp_phys,dtend_temp_nophys,ugrd,dtend_u_pbl,dtend_u_orogwd,dtend_u_deepcnv,dtend_u_cnvgwd,dtend_u_shalcnv,dtend_u_phys,dtend_u_nophys,vgrd,dtend_v_pbl,dtend_v_orogwd,dtend_v_deepcnv,dtend_v_cnvgwd,dtend_v_shalcnv,dtend_v_phys,dtend_v_nophys -d time,0,2 $historyfile `basename $historyfile`
ncks -v grid_xt,grid_yt,grid_lont,grid_latt,area $gridspec $gridspec
