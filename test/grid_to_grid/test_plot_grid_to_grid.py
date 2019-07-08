"""Tests used to establish the expected behavior of the plotting
   script plot_grid_to_grid.  These tests use the sample data that is
   available on the host 'eyewall' under the /d1/METplus_Plotting_Data/grid_to_grid
   directory.  On 'dakota', this same sample data is available under the
   /d4/METplus_Plotting_Data/grid_to_grid directory.

"""

import os
import pytest
# Import used to perform image_comparison with an identified baseline of plots.
# from matplotlib.testing.decorators import image_comparison
import plot_grid_to_grid as pgg


@pytest.fixture()
def settings():
    # set up with the values that are in plot_grid_to_grid.py to run "out of the box"
    settings_dict = {'input_dir': '/d1/METplus_Plotting_Data/grid_to_grid/201706130000/grid_stat',
                     'output_dir': '/d1/METplus_Plotting_Data/grid_to_grid/201706130000/grid_stat/plots',
                     'var': 'TMP', 'nc_fcst_var': '2017061300 FCST TMP P850 FULL', 'nc_fcst_title': '',
                     'nc_obs_var': 'OBS_TMP_P850_FULL', 'nc_obs_title': '2017061300 OBS TMP P850 FULL',
                     'nc_diff_var': 'DIFF_TMP_P850_TMP_P850_FULL', 'nc_diff_title': '2017061300 DIFF TMP P850 FULL'}

    print("plot settings used to plot TMP...")
    return settings_dict


def get_filesizes(input_dir):
    """
        This is used to get the file sizes of a list of files (full path)
        in a specified directory.
    :param input_dir: The specified directory that contains expected
                      plots whose file sizes are to be determined.
    :return: filesizes:  A dictionary whose keys are the full filepath
                         and corresponding value is the file size as
                         returned by os.stat(file).st_size.
    """
    all_files = []
    for root, dirs, files in os.walk(input_dir):
        for cur_file in files:
            if cur_file.endswith('png'):
                all_files.append(os.path.join(root, cur_file))

    # Create a dictionary that contains the file size for each expected file
    # based on filename (key) and filesize (values)
    file_sizes = {os.path.basename(cur_file): os.stat(cur_file).st_size for cur_file in all_files}
    return file_sizes



def test_expected_files_created(settings):
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

    :param settings:
    :return:
    """
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
        assert (expected in all_files)


def test_expected_filesizes(settings):
    """ Tests that of the six expected files (from using the sample data on 'eyewall'),
        the file sizes of the generated png files match with the file sizes of the
        expected files.
    """
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

    # File sizes of the expected files and created files (as returned by os.stat().st_size
    baseline_dir = '/d1/METplus_Plotting_Data/grid_to_grid/201706130000/grid_stat/baseline'
    expected_filesizes = get_filesizes(baseline_dir)
    created_files_filesizes = get_filesizes(output_dir)

    # Verify that the file sizes in the baseline plots match the filesizes of the
    # corresponding plots that were just created.
    for filename, sizes in expected_filesizes.items():
        if filename in created_files_filesizes:
            assert(expected_filesizes[filename] == created_files_filesizes[filename])
        else:
            assert(False)
