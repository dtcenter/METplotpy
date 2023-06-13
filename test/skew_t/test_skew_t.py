import os
import pytest
import shutil

from metplotpy.plots.skew_t import skew_t
# from metcalcpy.compare_images import \
#     CompareImages

@pytest.fixture
def setup():
    custom_config_filename = "./test_skew_t.yaml"

    # Invoke the command to generate askew-T diagram based on
    # the test_skew_t.yaml custom config file.
    # Retrieve the contents of the custom config file to over-ride
    # or augment settings defined by the default config file.
    skew_t.main(custom_config_filename)



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
    cur_dir = os.getcwd()
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


    expected_hours_ssh_162023_2023030100 = range(0, 175, 6)
    expected_hours_ssh_052023_2023030100 = range (0, 61, 6)
    # Create filenames of the expected output from ssh162023
    expected_filenames_ssh162023_start = 'ssh162023_avno_doper_2023030100'
    expected_filenames_ssh052023_start = 'ssh052023_avno_doper_2023010100'
    file_end = '_hr.png'
    expected_filenames_ssh162023 = []
    expected_filenames_ssh052023 = []

    # Create filename of the expected output from ssh052023
    for hr in expected_hours_ssh_052023_2023030100:
        filename_start = expected_filenames_ssh052023_start + "_diag_"
        filename = filename_start + str(hr) + file_end
        expected_filenames_ssh052023.append(filename)
    num_ssh_052023_expected = len(expected_filenames_ssh052023)

    # Create filename of the expected output from ssh162023
    for hr in  expected_hours_ssh_162023_2023030100:
        filename_start = expected_filenames_ssh162023_start + "_diag_"
        filename = filename_start + str(hr) + file_end
        expected_filenames_ssh162023.append(filename)
    num_ssh162023_expected = len(expected_filenames_ssh162023)

    num_sh052023 = 0
    num_sh162023 = 0
    for skewt_file in files_of_interest:
        if skewt_file in expected_filenames_ssh052023:
            num_sh052023 = num_sh052023 + 1
        elif skewt_file in expected_filenames_ssh162023:
            num_sh162023 = num_sh162023 + 1


    assert num_ssh_052023_expected == num_sh052023
    assert num_ssh162023_expected == num_sh162023

    # Clean up all png files
    shutil.rmtree(output_dir)
    shutil.rmtree('./logs')
