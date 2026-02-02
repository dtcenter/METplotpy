import os
import math
import pandas as pd

from metplotpy.plots.scatter import scatter as scatter

"""
   Test for the scatter plot 
"""

def test_scatter(module_setup_env, remove_files):
    """
        Generate a scatter plot from reformatted MPR Usecase data and
        check that the plot file is created, the dump points file is created
        and the dump points file has some expected values (looking at the
        first row of data).  Clean up the output directory when finished.

    """
    # note: scatter_log.txt does not appear to be created
    expected_files = [
        "scatter_mpr_tmp_obs_lat.png",
        "plot_points.txt",
    ]
    remove_files(os.environ['TEST_OUTPUT'], expected_files)

    scatter.main(f"{os.environ['TEST_DIR']}/test_scatter_mpr.yaml")

    for expected_file in expected_files:
        assert os.path.isfile(f"{os.environ['TEST_OUTPUT']}/{expected_file}")

    # Verify that the dump point file, plot_points.txt has expected points
    dump_points_file = os.path.join(os.environ['TEST_OUTPUT'], 'plot_points.txt')

    df = pd.read_csv(dump_points_file, sep='\t', skiprows=0)
    # expected x, y, and z values for the first row
    expected_x = 266.52143
    expected_y = 267.45001
    expected_z = 50.68000
    assert math.isclose( df.iloc[0,0], expected_x )
    assert math.isclose(df.iloc[0,1], expected_y)
    assert math.isclose(df.iloc[0,2], expected_z)
