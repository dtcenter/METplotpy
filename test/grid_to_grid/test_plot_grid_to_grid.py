from matplotlib.testing.decorators import image_comparison
import matplotlib.pyplot as plt
import pytest
import plot_grid_to_grid as pgg
import os


@pytest.fixture()
def settings():
    settings_dict = {'input_dir': '/d1/METplus_Plotting_Data/grid_to_grid/201706130000/grid_stat',
                     'output_dir': '/d1/METplus_Plotting_Data/grid_to_grid/201706130000/grid_stat/plots',
                     'var': 'TMP', 'nc_fcst_var': '2017061300 FCST TMP P850 FULL', 'nc_fcst_title': '',
                     'nc_obs_var': 'OBS_TMP_P850_FULL', 'nc_obs_title': '2017061300 OBS TMP P850 FULL',
                     'nc_diff_var': 'DIFF_TMP_P850_TMP_P850_FULL', 'nc_diff_title': '2017061300 DIFF TMP P850 FULL'}

    print("plot settings used to plot TMP...")
    return settings_dict


def test_expected_files_created(settings):
    ''' Requesting the OBS plots for the TMP variable should
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

    :param settings:
    :return:
    '''
    input_dir = settings['input_dir']
    output_dir = settings['output_dir']
    var = settings['var']
    nc_obs_var = settings['nc_obs_var']
    nc_obs_title = settings['nc_obs_title']


    # Genearate the OBS plots
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

    # Get all the files that are in the /d1/METplus_Plotting_Data/grid_to_grid/201706130000/grid_stat/plots directory
    # and verify that the 6 plots we are expecting are found in that directory.
    for root, dirs, files in os.walk(output_dir):
        all_files = [file for file in files]

    expected_files = ['TMP_OBS_grid_stat_GFS_vs_ANLYS_240000L_20170613_000000V_pairs.png',
                      'TMP_OBS_grid_stat_GFS_vs_ANLYS_480000L_20170613_000000V_pairs.png',
                      'TMP_DIFF_grid_stat_GFS_vs_ANLYS_240000L_20170613_000000V_pairs.png',
                      'TMP_DIFF_grid_stat_GFS_vs_ANLYS_480000L_20170613_000000V_pairs.png',
                      'TMP_FCST_grid_stat_GFS_vs_ANLYS_240000L_20170613_000000V_pairs.png',
                      'TMP_FCST_grid_stat_GFS_vs_ANLYS_480000L_20170613_000000V_pairs.png']

    for expected in expected_files:
        assert (expected in all_files)


