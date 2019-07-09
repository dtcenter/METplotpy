"""Tests for the plot_series_by_lead.py script and the
   animate_series_by_lead_all.py, using the
   sample data in the /d1/METplus_Plotting_Data directory
   on the host 'eyewall'.

"""

import os
import errno
import pytest
import plot_series_by_lead_all as psla

@pytest.fixture()
def settings():

    settings_dict = {'input_dir_base': '/d1/METplus_Plotting_Data/series_by_lead_all_fhrs',
                     'output_dir_base': '/d1/METplus_Plotting_Data/series_by_lead_all_fhrs/output'
                     }

    # create the output directory if it doesn't exist
    # (equivalent of Unix/Linux 'mkdir -p')
    try:
        os.makedirs(settings_dict['output_dir_base'])
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(settings_dict['output_dir_base']):
            pass

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

def test_get_info(settings):
    """
        Verify that the get_info() function in plot_series_by_lead_all.py
        is returning the correct number and files (based on filenames) produced
        by the series analysis by lead for all fhrs.

    """
    input_dir_base = settings['input_dir_base']
    output_dir_base = settings['output_dir_base']
    series_by_lead_tuples = psla.get_info(input_dir_base,
                                          output_dir_base)

    # iterate over each item in the list of named tuples and from the output_filename,
    # create the full filename (with .nc extension) and see if all the expected
    # files were found.
    expected_nc_files = ['/d1/METplus_Plotting_Data/series_by_lead_all_fhrs/output/series_F006_TMP_P850.nc',
                         '/d1/METplus_Plotting_Data/series_by_lead_all_fhrs/output/series_F006_HGT_P500.nc',
                         '/d1/METplus_Plotting_Data/series_by_lead_all_fhrs/output/series_F000_HGT_P500.nc',
                         '/d1/METplus_Plotting_Data/series_by_lead_all_fhrs/output/series_F000_TMP_P850.nc',
                         '/d1/METplus_Plotting_Data/series_by_lead_all_fhrs/output/series_F012_HGT_P500.nc',
                         '/d1/METplus_Plotting_Data/series_by_lead_all_fhrs/output/series_F012_TMP_P850.nc'
                         ]

    # Verify that we have found the number of netcdf files that were
    # expected (from running the feature relative use case corresponding
    # to using the series_by_lead_all_fhrs.conf).
    num_expected = len(expected_nc_files)
    cur_nc_counter = 0
    for cur_file in series_by_lead_tuples:
        cur_nc = cur_file.output_filename + ".nc"
        if cur_nc in expected_nc_files:
            cur_nc_counter = cur_nc_counter + 1

    assert(cur_nc_counter == num_expected)






def test_expected_files_created(settings):
    """
        Testing that the expected png files for OBAR and FBAR are created in
        the expected directory:
        /d1/METplus_Plotting_Data/series_by_lead_all_fhrs/output/series_F000_HGT_P500_fbar.png
        /d1/METplus_Plotting_Data/series_by_lead_all_fhrs/output/series_F000_HGT_P500_obar.png
        /d1/METplus_Plotting_Data/series_by_lead_all_fhrs/output/series_F000_TMP_P850_fbar.png
        /d1/METplus_Plotting_Data/series_by_lead_all_fhrs/output/series_F000_TMP_P850_obar.png
        /d1/METplus_Plotting_Data/series_by_lead_all_fhrs/output/series_F006_HGT_P500_fbar.png
        /d1/METplus_Plotting_Data/series_by_lead_all_fhrs/output/series_F006_HGT_P500_obar.png
        /d1/METplus_Plotting_Data/series_by_lead_all_fhrs/output/series_F006_TMP_P850_fbar.png
        /d1/METplus_Plotting_Data/series_by_lead_all_fhrs/output/series_F006_TMP_P850_obar.png
        /d1/METplus_Plotting_Data/series_by_lead_all_fhrs/output/series_F012_HGT_P500_fbar.png
        /d1/METplus_Plotting_Data/series_by_lead_all_fhrs/output/series_F012_HGT_P500_obar.png
        /d1/METplus_Plotting_Data/series_by_lead_all_fhrs/output/series_F012_TMP_P850_fbar.png
        /d1/METplus_Plotting_Data/series_by_lead_all_fhrs/output/series_F012_TMP_P850_obar.png

    :param settings: The dictionary that holds the input variable settings
    :return:
    """

    # Get all the series analysis files created by the use case,
    # and generate the plots.  Then compare the number and
    # filenames against a baseline directory to verify that
    # we are getting the same results.
    series_tuples = psla.get_info(settings['input_dir_base'],
                                  settings['output_dir_base'])

    expected_plots = [
        '/d1/METplus_Plotting_Data/series_by_lead_all_fhrs/output/series_F000_HGT_P500_fbar.png',
        '/d1/METplus_Plotting_Data/series_by_lead_all_fhrs/output/series_F000_HGT_P500_obar.png',
        '/d1/METplus_Plotting_Data/series_by_lead_all_fhrs/output/series_F000_TMP_P850_fbar.png',
        '/d1/METplus_Plotting_Data/series_by_lead_all_fhrs/output/series_F000_TMP_P850_obar.png',
        '/d1/METplus_Plotting_Data/series_by_lead_all_fhrs/output/series_F006_HGT_P500_fbar.png',
        '/d1/METplus_Plotting_Data/series_by_lead_all_fhrs/output/series_F006_HGT_P500_obar.png',
        '/d1/METplus_Plotting_Data/series_by_lead_all_fhrs/output/series_F006_TMP_P850_fbar.png',
        '/d1/METplus_Plotting_Data/series_by_lead_all_fhrs/output/series_F006_TMP_P850_obar.png',
        '/d1/METplus_Plotting_Data/series_by_lead_all_fhrs/output/series_F012_HGT_P500_fbar.png',
        '/d1/METplus_Plotting_Data/series_by_lead_all_fhrs/output/series_F012_HGT_P500_obar.png',
        '/d1/METplus_Plotting_Data/series_by_lead_all_fhrs/output/series_F012_TMP_P850_fbar.png',
        '/d1/METplus_Plotting_Data/series_by_lead_all_fhrs/output/series_F012_TMP_P850_obar.png']

    num_expected = len(expected_plots)
    plot_background_map = True
    for cur_tuple in series_tuples:
        hour = cur_tuple.fhr
        fhr = 'series_F' + cur_tuple.fhr
        input_dir = os.path.join(settings['input_dir_base'], fhr)
        level_type = cur_tuple.level_type
        level = cur_tuple.level
        variable_name = cur_tuple.variable
        output_filename = cur_tuple.output_filename
        input_filename = 'series_F' + hour + '_' + variable_name + '_' + level_type + \
                         level + '.nc'
        input_file = os.path.join(input_dir, input_filename)
        psla.generate_plot(input_dir, input_file, hour, variable_name, level_type, level,
                      output_filename, plot_background_map)


    # Now verify that the same number of files and the same
    # files (png) have been created by the call to generate_plot.
    baseline_dir = '/d1/METplus_Plotting_Data/series_by_lead_all_fhrs/baseline_output'
    expected_filesizes = get_filesizes(baseline_dir)
    created_files_filesizes = get_filesizes(settings['output_dir_base'])
    # Verify that the file sizes in the baseline plots match the filesizes of the
    # corresponding plots that were just created.
    for filename, sizes in expected_filesizes.items():
        if filename in created_files_filesizes:
            assert (expected_filesizes[filename] == created_files_filesizes[filename])
        else:
            assert (False)


