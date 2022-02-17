"""Tests used to establish the expected behavior of the plotting
   script plot_grid_to_grid.  These tests use the sample data that is
   available on the host 'kiowa' under the /d1/projects/METplus/METplus_Plotting_Data/grid_to_grid
   directory.
"""

import os, sys
import pytest
import yaml
# Import used to perform image_comparison with an identified baseline of plots.
# from matplotlib.testing.decorators import image_comparison
#sys.path.append("../..")
#from metplotpy.contributed.grid_to_grid.plot_grid_to_grid import PlotGridToGrid


@pytest.mark.skip("only to be run on host with large dataset. Requires special packages, uncomment import to run")
def test_expected_files_created():
    """
        Testing that the expected png
        Requesting the OBS plots for the TMP variable should
        produce the following two files in the /d1/METplus_Plotting_Data/grid_to_grid/201706130000/grid_stat/plots
        directory:
        TMP_OBS_grid_stat_GFS_vs_ANLYS_240000L_20170613_000000V_pairs.png
        TMP_OBS_grid_stat_GFS_vs_ANLYS_480000L_20170613_000000V_pairs.png

        and requesting the DIFF plots for the TMP variable should produce these files in the same directory:
        TMP_DIFF_grid_stat_GFS_vs_ANLYS_240000L_20170613_000000V_pairs.png
        TMP_DIFF_grid_stat_GFS_vs_ANLYS_480000L_20170613_000000V_pairs.png

        and requesting the FCST plots should produce the following files in the same directory:
        TMP_FCST_grid_stat_GFS_vs_ANLYS_240000L_20170613_000000V_pairs.png
        TMP_FCST_grid_stat_GFS_vs_ANLYS_480000L_20170613_000000V_pairs.png


    :return:
    """
    config_file = "./grid.yaml"

    with open(config_file, 'r') as stream:
        try:
            config = yaml.load(stream, Loader=yaml.FullLoader)
        except yaml.YAMLError as exc:
            print(exc)

    # Invoke the function that generates the plot
    pgg = PlotGridToGrid(config)

    input_dir = pgg.config['input_dir']
    output_dir = pgg.config['output_dir']
    var = pgg.config['var']
    nc_obs_var = pgg.config['nc_obs_var']
    nc_obs_title = pgg.config['nc_obs_title']

    # Generate the OBS plots
    nc_flag_type = 'OBS'
    background_on = True
    pgg.create_plots(input_dir, var, nc_obs_var, nc_obs_title, nc_flag_type, output_dir, background_on)

    # Genearate the DIFF plots
    nc_flag_type = 'DIFF'
    background_on = True
    pgg.create_plots(input_dir, var, nc_obs_var, nc_obs_title, nc_flag_type, output_dir, background_on)

    # Genearate the FCST plots
    nc_flag_type = 'FCST'
    background_on = True
    pgg.create_plots(input_dir, var, nc_obs_var, nc_obs_title, nc_flag_type, output_dir, background_on)

    # Get all the files that are in the
    #  /d1/projects/METplus/METplus_Plotting_Data/grid_to_grid/201706130000/grid_stat/plots directory
    # and verify that the 6 plots we are expecting are found in that directory.
    all_files = []
    for root, dirs, files in os.walk(output_dir):
        for cur_file in files:
            if cur_file.endswith('png'):
               all_files.append(cur_file)


    expected_files = ['TMP_OBS_grid_stat_GFS_vs_ANLYS_240000L_20170613_000000V_pairs.png',
                      'TMP_OBS_grid_stat_GFS_vs_ANLYS_480000L_20170613_000000V_pairs.png',
                      'TMP_DIFF_grid_stat_GFS_vs_ANLYS_240000L_20170613_000000V_pairs.png',
                      'TMP_DIFF_grid_stat_GFS_vs_ANLYS_480000L_20170613_000000V_pairs.png',
                      'TMP_FCST_grid_stat_GFS_vs_ANLYS_240000L_20170613_000000V_pairs.png',
                      'TMP_FCST_grid_stat_GFS_vs_ANLYS_480000L_20170613_000000V_pairs.png']



    for expected in expected_files:
         if expected not in all_files:
             assert False
    # if we get here, all the expected files were created
    assert True

if __name__ == "__main__":
    # test_expected_files_created()
    pass
