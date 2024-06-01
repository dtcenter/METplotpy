import os
import math
import shutil
import pandas as pd
import yaml
from METplotpy.metplotpy.plots.scatter import scatter as sc

"""
   Test for the scatter plot 
"""

def read_config(config_filename) -> dict:
    """
        Args:
           @param config_filename: The name of the YAML config file

        Returns:
           parms: a dictionary representation of the YAML config file
    """
    with open(config_filename, 'r') as stream:
            try:
                parms = yaml.load(stream, Loader=yaml.FullLoader)
                return parms
            except yaml.YAMLError as exc:
                print(exc)
def test_files_exist():
    """
        Generate a scatter plot from reformatted MPR Usecase data and
        check that the plot file is created, the dump points file is created
        and the dump points file has some expected values (looking at the
        first row of data).  Clean up the output directory when finished.

    """
    os.environ['METPLOTPY_BASE'] = "../../"
    test_config_filename = os.path.join(os.getcwd(), "test_scatter_mpr.yaml")
    sc.main(test_config_filename)

    # Verify that the plot was generated
    plot_file = "scatter_mpr_tmp_obs_lat.png"
    path = os.path.join(os.getcwd(), 'output')
    fullpath = os.path.join(path, plot_file)
    assert os.path.isfile(fullpath) == True

    # Verify that the dump point file, plot_points.txt was generated and has expected points
    dump_points_file = os.path.join(path, 'plot_points.txt')
    assert os.path.isfile(dump_points_file) == True

    df = pd.read_csv(dump_points_file, sep='\t', skiprows=0)
    # expected x, y, and z values for the first row
    expected_x = 266.52143
    expected_y = 267.45001
    expected_z = 50.68000
    assert math.isclose( df.iloc[0,0], expected_x )
    assert math.isclose(df.iloc[0,1], expected_y)
    assert math.isclose(df.iloc[0,2], expected_z)

    # clean up files in the output directory and
    # the output directory
    shutil.rmtree(os.path.join(os.getcwd(), 'output'))
