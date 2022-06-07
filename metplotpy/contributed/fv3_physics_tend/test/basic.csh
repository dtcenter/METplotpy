#!/bin/csh

set echo 
conda activate
cd /glade/scratch/ahijevyc/METplotpy/metplotpy/contributed/fv3_physics_tend
# plan view of PBL
python planview_fv3.py /glade/scratch/mwong/dave/sample_cases/CONUS_25km_GFSv15p2/2019050412/fv3_history.nc /glade/scratch/mwong/dave/sample_cases/CONUS_25km_GFSv15p2/2019050412/grid_spec.nc tmp pbl -t 6 -v 20190504T21
# plan view of all tendencies near 500 hPa
python planview_fv3.py /glade/scratch/mwong/dave/sample_cases/CONUS_25km_GFSv15p2/2019050412/fv3_history.nc /glade/scratch/mwong/dave/sample_cases/CONUS_25km_GFSv15p2/2019050412/grid_spec.nc tmp -p 500 -t 6 -v 20190504T21
python cross_section_vert.py /glade/scratch/mwong/dave/sample_cases/CONUS_25km_GFSv15p2/2019050412/fv3_history.nc /glade/scratch/mwong/dave/sample_cases/CONUS_25km_GFSv15p2/2019050412/grid_spec.nc tmp -t 6 -v 20190504T21 -s 32 -115 -e 34 -82
python vert_profile_fv3.py /glade/scratch/mwong/dave/sample_cases/CONUS_25km_GFSv15p2/2019050412/fv3_history.nc /glade/scratch/mwong/dave/sample_cases/CONUS_25km_GFSv15p2/2019050412/grid_spec.nc tmp -t 6 -v 20190504T21 -s test/MID_CONUS
