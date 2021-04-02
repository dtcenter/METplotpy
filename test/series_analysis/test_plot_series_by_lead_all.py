"""Tests for the plot_series_by_lead.py script and the
   animate_series_by_lead_all.py, using the
   sample data in the /d1/METplus_Plotting_Data directory
   on the host 'eyewall'.

"""

import os, sys
import yaml
import errno
import pytest
sys.path.append("../../")
import plots.util as util
from contributed.series_analysis.plot_series_by_lead_all import PlotSeriesByLeadAll

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
    expected_files = [
        '/Volumes/d1/minnawin/METplus_Plotting_Output/series_by_lead_all_fhrs/output/series_F000_to_F000_TMP_Z2',
        '/Volumes/d1/minnawin/METplus_Plotting_Output/series_by_lead_all_fhrs/output/series_F018_to_F018_TMP_Z2',
        '/Volumes/d1/minnawin/METplus_Plotting_Output/series_by_lead_all_fhrs/output/series_F024_to_F024_TMP_Z2',
        '/Volumes/d1/minnawin/METplus_Plotting_Output/series_by_lead_all_fhrs/output/series_F042_to_F042_TMP_Z2'
        ]

    # Verify that we have found the number of netcdf files that were
    # expected (from running the feature relative use case corresponding
    # to using the series_by_lead_all_fhrs.conf).
    num_expected = len(expected_files)
    match_counter = 0
    for cur_file in series_by_lead_tuples:
        if cur_file.output_filename in expected_files:
            match_counter = match_counter + 1

    assert (match_counter == num_expected)



