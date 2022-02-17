"""Tests for the plot_series_by_lead.py script and the
   animate_series_by_lead_all.py, using the
   sample data in the /d1/METplus_Plotting_Data directory
   on the host 'eyewall'.

"""

import os, sys, re
import pytest
import yaml
sys.path.append("../../")
# from metplotpy.contributed.series_analysis.plot_series_by_lead_all import PlotSeriesByLeadAll
# from metplotpy.contributed.series_analysis.plot_series_by_grouping import PlotSeriesByGrouping
# from metplotpy.contributed.series_analysis.animate_series_by_lead_all import AnimateSeriesByLeadAll
# from metplotpy.contributed.series_analysis import animate_utilities as au

@pytest.mark.skip("needs special packages and large dataset to run")
def test_get_info():
    """
        Verify that the get_info() function in plot_series_by_lead_all.py
        is returning the correct number and files (based on filenames) produced
        by the series analysis by lead for all fhrs.

    """


    config_file = "./series_lead_all.yaml"

    with open(config_file, 'r') as stream:
        try:
            config = yaml.load(stream, Loader=yaml.FullLoader)
        except yaml.YAMLError as exc:
            print(exc)

    psla = PlotSeriesByLeadAll(config)
    input_dir_base = psla.config['input_nc_file_dir']
    output_dir_base = psla.config['output_dir']
    series_by_lead_tuples = psla.get_info(input_dir_base,
                                          output_dir_base)

    # iterate over each item in the list of named tuples and from the output_filename,
    # create the full filename (with .nc extension) and see if all the expected
    # files were found.
    expected_filenames = ['series_F000_to_F000_TMP_Z2', 'series_F018_to_F018_TMP_Z2',
                          'series_F024_to_F024_TMP_Z2', 'series_F042_to_F042_TMP_Z2']
    expected_files = []
    for filenm in expected_filenames:
        full_filename = os.path.join(output_dir_base, filenm)
        expected_files.append(full_filename)

    # Verify that we have found the number of netcdf files that were
    # expected (from running the feature relative use case corresponding
    # to using the series_by_lead_all_fhrs.yaml).
    num_expected = len(expected_files)
    match_counter = 0
    for cur_file in series_by_lead_tuples:
        if cur_file.output_filename in expected_files:
            match_counter = match_counter + 1

    assert (match_counter == num_expected)

@pytest.mark.skip("needs special packages and large dataset to run")
def test_series_lead_group_plots():
    ''' Test that the expected png files are created by the plot_series_by_grouping module'''

    config_file = "./series_lead_group.yaml"

    with open(config_file, 'r') as stream:
        try:
            config = yaml.load(stream, Loader=yaml.FullLoader)
        except yaml.YAMLError as exc:
            print(exc)

    psg = PlotSeriesByGrouping(config)
    input_nc_file_dir = psg.config['input_nc_file_dir']
    output_dir = psg.config['output_dir']
    background_on_setting = psg.config['background_on']
    if background_on_setting.upper()  == 'TRUE':
        background_on = True
    else:
        background_on = False

    filename_regex = psg.config['png_plot_filename_regex']
    expected_filenames = [
        'series_F000_to_F018_TMP_Z2_fbar.png',
        'series_F000_to_F018_TMP_Z2_obar.png',
        'series_F024_to_F042_TMP_Z2_fbar.png',
        'series_F024_to_F042_TMP_Z2_obar.png'
    ]

    expected_files = []
    for filenm in expected_filenames:
        full_filename = os.path.join(output_dir, filenm)
        expected_files.append(full_filename)

    psg.create_plots(input_nc_file_dir, output_dir, background_on, filename_regex)

    # Verify that we have found the number of png files that were
    # expected (from running the feature relative use case corresponding
    # to using the series_lead_group.yaml).
    match_counter = 0
    for root, dirs, files in os.walk(output_dir):
        for file in files:
            # match = re.search('series_F([0-9]{3})_(HGT|TMP)_(P|Z)([0-9]{3}).nc', file)
            match = re.search('series_F([0-9]{1,3})_to_F([0-9]{1,3})_(HGT|TMP)_(P|Z)([0-9]{1,3})(.*).png', file)
            if match:
                full_file = os.path.join(output_dir, file)
                match_counter += 1

    num_expected = len(expected_files)

    # print("Number of matches: ", match_counter)
    assert (match_counter == num_expected)

@pytest.mark.skip("needs special packages and large dataset to run")
def test_series_lead_group_animations():
    ''' Test that the expected gif files (animations) are created by the plot_series_by_grouping module'''

    config_file = "./series_lead_group.yaml"

    with open(config_file, 'r') as stream:
        try:
            config = yaml.load(stream, Loader=yaml.FullLoader)
        except yaml.YAMLError as exc:
            print(exc)

    psg = PlotSeriesByGrouping(config)
    input_nc_file_dir = psg.config['input_nc_file_dir']
    output_dir = psg.config['output_dir']
    background_on_setting = psg.config['background_on']
    if background_on_setting.upper()  == 'TRUE':
        background_on = True
    else:
        background_on = False

    filename_regex = psg.config['png_plot_filename_regex']
    expected_filenames = [
        'series_TMP_Z2_fbar.gif','series_TMP_Z2_obar.gif']

    expected_files = []
    for filenm in expected_filenames:
        full_filename = os.path.join(output_dir, filenm)
        expected_files.append(full_filename)

    psg.create_plots(input_nc_file_dir, output_dir, background_on, filename_regex)

    # Verify that we have found the number of png files that were
    # expected (from running the feature relative use case corresponding
    # to using the series_lead_group.yaml).
    match_counter = 0
    for root, dirs, files in os.walk(output_dir):
        for file in files:
            # match = re.search('series_F([0-9]{3})_(HGT|TMP)_(P|Z)([0-9]{3}).nc', file)
            match = re.search('series_(HGT|TMP)_(P|Z)([0-9]{1,3})(.*).gif', file)
            if match:
                full_file = os.path.join(output_dir, file)
                match_counter += 1

    num_expected = len(expected_files)
    assert (match_counter == num_expected)

@pytest.mark.skip("needs special packages and large dataset to run")
def test_animation_series_by_lead():
    ''' Test that the expected gif files (animations) are created by the
        animate_series_by_lead module.
    '''

    config_file = "./animate.yaml"

    with open(config_file, 'r') as stream:
        try:
            config = yaml.load(stream, Loader=yaml.FullLoader)
        except yaml.YAMLError as exc:
            print(exc)

    asbl = AnimateSeriesByLeadAll(config)
    # Get the values that were set in the yaml config file animate.yaml
    input_dir = asbl.config['input_dir']
    output_dir = asbl.config['output_dir']
    fhrs_list = asbl.config['fhrs_list']
    variable = asbl.config["variable"]
    level_type = asbl.config['level_type']
    level = asbl.config['level']
    filename_regex = asbl.config['filename_regex']
    animation_duration_secs = asbl.config['animation_duration_secs']
    # list of statistics of interest
    statistics_of_interest = asbl.config['statistic_of_interest']

    # Animate the plots corresponding to the statistics of interest for the corresponding forecast, variable, and level
    for statistic in statistics_of_interest:
        stat_files = asbl.collect_files_to_animate(input_dir, fhrs_list, variable,
                                                   level_type, level, statistic)
        # create output filename for statistic animation (gif) file
        output_filename = asbl.create_output_filename(output_dir, stat_files[0], filename_regex)
        au.create_gif(animation_duration_secs, stat_files, output_filename)

    expected_filenames = [
        '/series_TMP_Z2_fbar.gif','/series_TMP_Z2_obar.gif']

    expected_files = []
    for filenm in expected_filenames:
        full_filename = os.path.join(output_dir, filenm)
        expected_files.append(full_filename)

    # Verify that we have found the number of png files that were
    # expected (from running the feature relative use case corresponding
    # to using the series_lead_group.yaml).
    match_counter = 0
    for root, dirs, files in os.walk(output_dir):
        for file in files:
            # match = re.search('series_F([0-9]{3})_(HGT|TMP)_(P|Z)([0-9]{3}).nc', file)
            match = re.search('series_(HGT|TMP)_(P|Z)([0-9]{1,3})(.*).gif', file)
            if match:
                full_file = os.path.join(output_dir, file)
                match_counter += 1

    num_expected = len(expected_files)

    # print("Number of matches: ", match_counter)
    assert (match_counter == num_expected)

