import os
import pytest
import shutil
import re

from metplotpy.plots.skew_t import skew_t as skew_t
# from metcalcpy.compare_images import  CompareImages



def test_files_exist():
    '''
        Checking that only the expected plot files are getting created and
        input files with only fill/missing data are not created.
    '''

    os.environ['METPLOTPY_BASE'] = "../../"
    cur_dir = os.getcwd()
    custom_config_filename = os.path.join(cur_dir, "test_skew_t.yaml")

    # Invoke the command to generate a skew-T  Diagram based on
    # the test_skew_tm.yaml custom config file.
    skew_t.main(custom_config_filename)

    # Verify that files for the ssh052023 data exists for the 0,6, 12,18,24, 30, 42,
    # 48, 54, and 60 hour data.
    output_dir = os.path.join(cur_dir, 'output' )

    # Some of these data files have incomplete data so check for the expected hour
    # plots.

    print(f"Output dir: {output_dir}")
    file_ext = '.png'
    files_of_interest = []
    for root, dir, files in os.walk(output_dir):
        for item in files:
            if item.endswith(file_ext):
                # print(f"Item of interest: {item}")
                full_file = os.path.join(root, item)
                base_file = os.path.basename(full_file)
                files_of_interest.append(base_file)

    # List of files for the sh052023 data (which is missing data for hours 66-240).
    data_some_missing_data = ['ssh052023_avno_doper_2023010100_diag',
                              'ssh052023_avno_doper_2023010106_diag']

    # Config file is requesting all the available sounding hours
    expected_hours_for_2023_010100 = range(0,61,6)
    expected_hours_for_2023_010106 = range(0,49,6)

    # Create a list of expected base file names with their expected hours.
    expected_base_filenames = []
    for base in data_some_missing_data:
        # Expected base for expected plot output name of format:
        # ssh_052023_avno_doper_202301010[0|6]_diag_[0-9]{1,2}_hr
        if base == 'ssh052023_avno_doper_2023010100_diag':
            # Working with the 2023010100 date file
            for cur_hr in expected_hours_for_2023_010100:
               base_hr = base + '_'  + str(cur_hr) + '_hr'
               expected_base_filenames.append(base_hr)

        elif base == 'ssh052023_avno_doper_2023010106_diag':
            # Working with the 2023010106 date
            for cur_hr in expected_hours_for_2023_010106:
               base_hr = base + '_' + str(cur_hr) + '_hr'
               expected_base_filenames.append(base_hr)

    # Subset only the files that correspond to the sh052023 data
    subset_files_of_interest = []
    for cur_file in files_of_interest:
        match_found = re.match(r'(ssh052023_.*).png', cur_file)
        if match_found:
            subset_files_of_interest.append(match_found.group(1))

    # Verify that the expected plots were generated.
    num_found = 0
    for expected in expected_base_filenames:
        if expected in subset_files_of_interest:
            num_found += 1

    if len(subset_files_of_interest) == num_found:
        assert True
    else:
        assert False


    # Clean up all png files
    temp_datafile = os.path.join(cur_dir, 'sounding_data.dat')
    os.remove(temp_datafile)
    shutil.rmtree(output_dir)
    # If running without the ' -p no:logging' option, then uncomment to ensure that log
    # files are removed.
    # shutil.rmtree('./logs')

def test_files_not_created():
    '''
        Checking that input files with only fill/missing data are not created.
    '''

    os.environ['METPLOTPY_BASE'] = "../../"
    cur_dir = os.getcwd()
    custom_config_filename = os.path.join(cur_dir, "test_skew_t.yaml")

    # Invoke the command to generate a skew-T  Diagram based on
    # the test_skew_tm.yaml custom config file.
    skew_t.main(custom_config_filename)

    # Verify that files for the ssh052023 data exists for the 0,6, 12,18,24, 30, 42,
    # 48, 54, and 60 hour data.
    output_dir = os.path.join(cur_dir, 'output' )

    # Some of these data files have incomplete data so check for the expected hour
    # plots.

    print(f"Output dir: {output_dir}")
    file_ext = '.png'
    files_of_interest = []
    for root, dir, files in os.walk(output_dir):
        for item in files:
            if item.endswith(file_ext):
                # print(f"Item of interest: {item}")
                full_file = os.path.join(root, item)
                base_file = os.path.basename(full_file)
                files_of_interest.append(base_file)

    # List of files with no sounding data (9999 for all fields and times)
    no_sounding_data = ['ssh162023_avno_doper_2023022712_diag',
                        'ssh162023_avno_doper_2023022800_diag',
                        'ssh162023_avno_doper_2023022806_diag',
                        'ssh162023_avno_doper_2023030706_diag']

    # Subset the files of interest to just sh162023 output.
    subsetted_files_of_interest = []
    for cur in files_of_interest:
        match = re.match(r'^ssh162023', cur)
        if match:
            subsetted_files_of_interest.append(cur)

    # Verify that there aren't any plots created for the files with missing sounding
    # data. First, create a list of the base names of the plots that were created and
    # that correspond to the input data of interest (i.e. the sh162023_*.dat data).
    subsetted_basenames = []
    for cur_plot in subsetted_files_of_interest:
        match = re.match(r'(ssh162023_avno_doper_20230[0-9]{5}_diag)_*._hr.png',
                         cur_plot)
        if match:
            subsetted_basenames.append(match.group(1))

    # Count how often we find a basename of a plot that we didn't expect to create with
    # the list of base names of plots that were created.
    fail_counter = 0
    for cur in no_sounding_data:
        if cur in subsetted_basenames:
            fail_counter += 1

    if fail_counter == 0:
        assert True
    else:
        assert False


    # Clean up all png files
    temp_datafile = os.path.join(cur_dir, 'sounding_data.dat')
    os.remove(temp_datafile)
    shutil.rmtree(output_dir)
    # If running with the ' -p no:logging' option, then uncomment to ensure that log
    # files are removed.
    # shutil.rmtree('./logs')


def test_empty_input():
    '''
        Checking that empty input file is not creating any plots.
    '''

    os.environ['METPLOTPY_BASE'] = "../../"
    cur_dir = os.getcwd()
    custom_config_filename = os.path.join(cur_dir, "test_skew_t.yaml")

    # Invoke the command to generate a skew-T  Diagram based on
    # the test_skew_tm.yaml custom config file.
    skew_t.main(custom_config_filename)

    # Verify that files for the ssh052023 data exists for the 0,6, 12,18,24, 30, 42,
    # 48, 54, and 60 hour data.
    output_dir = os.path.join(cur_dir, 'output')

    # Some of these data files have incomplete data so check for the expected hour
    # plots.

    print(f"Output dir: {output_dir}")
    file_ext = '.png'
    files_of_interest = []
    for root, dir, files in os.walk(output_dir):
        for item in files:
            if item.endswith(file_ext):
                # print(f"Item of interest: {item}")
                full_file = os.path.join(root, item)
                base_file = os.path.basename(full_file)
                files_of_interest.append(base_file)

    # List of empty files
    no_data_empty_file = ['sal092022_avno_doper_2022092800_diag']

    # Verify that there aren't any plots created for the file with missing sounding
    # data.

    # First, subset the files of interest to just sal0920223 output.
    subsetted_files_of_interest = []
    for cur in files_of_interest:
        match = re.match(r'^sal092022', cur)
        if match:
            subsetted_files_of_interest.append(cur)

    match_found = re.match(r'^sal092022_avno_doper_2022092800_diag',
                            no_data_empty_file[0])
    if match_found in subsetted_files_of_interest:
        # The output file was created when it shouldn't have been, fail.
        assert False
    else:
        # The output file was NOT created, as expected. Pass.
        assert True

    # Clean up all png files
    temp_datafile = os.path.join(cur_dir, 'sounding_data.dat')
    os.remove(temp_datafile)
    shutil.rmtree(output_dir)
    # If running without the ' -p no:logging' option, then uncomment to ensure that log
    # files are removed.
    # shutil.rmtree('./logs')
