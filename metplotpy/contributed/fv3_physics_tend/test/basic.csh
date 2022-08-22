#!/bin/csh

conda activate
set echo 
cd /glade/scratch/ahijevyc/METplotpy/metplotpy/contributed/fv3_physics_tend
set config=../../../test/fv3_physics_tend/fv3_physics_tend_defaults.yaml
# plan view of PBL
python planview_fv3.py       $config test/fv3_history.nc test/grid_spec.nc tmp pbl -t 1 -v 20190504T13
# plan view of all tendencies near 500 hPa
python planview_fv3.py       $config test/fv3_history.nc test/grid_spec.nc tmp pbl -p 500 -t 1 -v 20190504T14
python cross_section_vert.py $config test/fv3_history.nc test/grid_spec.nc tmp     -t 2 -v 20190504T14 -s 32 -115 -e 34 -82
python vert_profile_fv3.py   $config test/fv3_history.nc test/grid_spec.nc tmp     -t 1 -v 20190504T14 -s test/MID_CONUS
