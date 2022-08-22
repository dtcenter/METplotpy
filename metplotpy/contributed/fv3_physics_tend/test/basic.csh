#!/bin/csh

conda activate
set echo 
setenv METPLOTPY_BASE /glade/scratch/ahijevyc/METplotpy
setenv CONFIG $METPLOTPY_BASE/test/fv3_physics_tend/fv3_physics_tend_defaults.yaml
setenv WORKING_DIR $METPLOTPY_BASE/metplotpy/contributed/fv3_physics_tend/test

cd $METPLOTPY_BASE/metplotpy/contributed/fv3_physics_tend
# plan view of all tendencies near 500 hPa
python planview_fv3.py       $CONFIG $WORKING_DIR/fv3_history.nc $WORKING_DIR/grid_spec.nc tmp pbl -p 500 -t 1 -v 20190504T14 --nofineprint
# plan view of PBL
python planview_fv3.py       $CONFIG $WORKING_DIR/fv3_history.nc $WORKING_DIR/grid_spec.nc tmp pbl -t 1 -v 20190504T13 --nofineprint
python vert_profile_fv3.py   $CONFIG $WORKING_DIR/fv3_history.nc $WORKING_DIR/grid_spec.nc tmp     -t 2 -v 20190504T14 -s $WORKING_DIR/MID_CONUS --nofineprint
python cross_section_vert.py $CONFIG $WORKING_DIR/fv3_history.nc $WORKING_DIR/grid_spec.nc tmp     -t 2 -v 20190504T14 -s 32 -115 -e 34 -82 --nofineprint
# difference plot
python vert_profile_fv3.py   $CONFIG $WORKING_DIR/fv3_history.nc $WORKING_DIR/grid_spec.nc tmp     -t 1 --subtract $WORKING_DIR/fv3_history.nc --nofineprint
