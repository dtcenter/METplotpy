#!/bin/bash

cd bar; python3 -m pytest
cd ../box; python3 -m pytest
cd ../contour; python3 -m pytest
cd ../difficulty_index; python3 -m pytest
cd ../eclv; python3 -m pytest
cd ../ens_ss; python3 -m pytest
cd ../equivalence_testing_bounds; python3 -m pytest
cd ../fv3_physics_tend; python3 -m pytest
cd ../grid_to_grid; python3 -m pytest
cd ../histogram; python3 -m pytest
cd ../histogram_2d; python3 -m pytest
cd ../hovmoeller; python3 -m pytest
cd ../line; python3 -m pytest
cd ../mpr_plot; python3 -m pytest
cd ../performance_diagram; python3 -m pytest
cd ../reliability_diagram; python3 -m pytest
cd ../revision_box; python3 -m pytest
cd ../taylor_diagram; python3 -m pytest
cd ../wind_rose; python3 -m pytest
