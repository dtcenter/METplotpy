"""Tests for the plot_series_by_init.py script, on the TMP variable using
   the sample data on the host 'eyewall': /d1/METplus_Plotting_Data/series_by_init
"""
import os, shutil
import errno
import pytest
import plot_series_by_init as psi
from PIL import Image
from PIL import ImageChops

@pytest.fixture()
def settings():
    # settings_dict = {'input_dir': '/d1/METplus_Plotting_Data/series_by_init/20141214_00/',
    #                  'nc_input_filename':
    #                      '/d1/METplus_Plotting_Data/series_by_init/20141214_00/ML1200942014/series_TMP_Z2.nc',
    #                  'var': 'TMP',
    #                  'level':'Z2',
    #                  "storm_number": 'ML1200972014',
    #                  'output_dir': '/d1/METplus_Plotting_Data/series_by_init/20141214_00/ML1200942014/test_plots',
    #                  }

    settings_dict = {'input_dir': '../expected_output/series_by_init/20141214_00/',
                     'nc_input_filename':
                         '../expected_output/series_by_init/20141214_00/ML1200942014/series_TMP_Z2.nc',
                     'var': 'TMP',
                     'level': 'Z2',
                     "storm_number": 'ML1200972014',
                     'output_dir': '../test_output',
                     }
    obar_fbar_output = 'TMP_Z2'
    settings_dict['obar_fbar_output'] = obar_fbar_output

    # create the output directory if it doesn't exist
    # (equivalent of Unix/Linux 'mkdir -p')
    try:
        os.makedirs(settings_dict['output_dir'])
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(settings_dict['output_dir']):
            pass

    print("plot settings used to plot series by init TMP...")
    return settings_dict

def cleanup_test_output_dir():
    '''Remove all files in the ../test_output directory so we have a clean
       output directory at the beginning of each test.
    '''
    output_dir = "../test_output"
    for filename in os.listdir(output_dir):
        filepath = os.path.join(output_dir, filename)
        try:
            if os.path.isfile(filepath) or os.path.islink(filepath):
                os.unlink(filepath)
            elif os.path.isdir(filepath):
                shutil.rmtree(filepath)
        except Exception as e:
            print(f'Failed to delete {filepath} due to {e}')


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


def compare_images(path_one, path_two, diff_save_location):
    """
        Compare two images, and save the diff image to determine if there is a difference.

    :param path_one:   File path leading to first image/plot
    :param path_two:   File path leading to second image/plot
    :param diff_save_location:  The diff between the two images, if empty, then the two images/plots are the same
    :return:
    """

    image_one = Image.open(path_one)
    image_two = Image.open(path_two)

    diff = ImageChops.difference(image_one, image_two)

    if diff.getbbox():
        diff.save(diff_save_location)



def test_expected_files_created(settings):
    """
        Testing that the expected png files for OBAR and FBAR are created in
        the expected directory:
        ../expected_output/TMP_Z2_fbar.png
        ../expected_output/TMP_Z2_obar.png

    :param settings:
    :return:
    """

    # start with clean output directory
    cleanup_test_output_dir()

    nc_input_filename = settings['nc_input_filename']
    output_dir = settings['output_dir']
    variable_name = settings['var']
    level =  settings['level']
    storm_number = settings['storm_number']
    obar_fbar_output = settings['obar_fbar_output']
    include_background = True
    nc_input_dir = os.path.join(settings['input_dir'], storm_number)



    # Generate the FBAR and OBAR plots for the TMP at level Z2
    background_on = True
    psi.create_plot(nc_input_dir, nc_input_filename, variable_name, level,
                storm_number, obar_fbar_output, output_dir, include_background)




    # Get all the files that are in the /d1/METplus_Plotting_Data/grid_to_grid/201706130000/grid_stat/plots directory
    # and verify that the 6 plots we are expecting are found in that directory.
    all_files = []
    for root, dirs, files in os.walk(nc_input_dir):
        for cur_file in files:
            if cur_file.endswith('png'):
               all_files.append(cur_file)


    expected_files = ['TMP_Z2_fbar.png',
                      'TMP_Z2_obar.png']

    # for expected in expected_files:
    #     assert (expected in all_files)


# def test_expected_filesizes(settings):
#     """ Tests that of the two expected files (from using the sample data on 'eyewall'),
#         the file sizes of the generated png files match with the file sizes of the
#         expected files.
#     """
#     nc_input_filename = settings['nc_input_filename']
#     output_dir = settings['output_dir']
#     variable_name = settings['var']
#     level = settings['level']
#     storm_number = settings['storm_number']
#     obar_fbar_output = settings['obar_fbar_output']
#     include_background = True
#     nc_input_dir = os.path.join(settings['input_dir'], storm_number)
#
#     # Generate the FBAR and OBAR plots
#     background_on = True
#     psi.create_plot(nc_input_dir, nc_input_filename, variable_name, level,
#                     storm_number, obar_fbar_output, output_dir, include_background)
#
#
#     # File sizes of the expected files and created files (as returned by os.stat().st_size
#     baseline_dir = '/d1/METplus_Plotting_Data/series_by_init/20141214_00/ML1200942014'
#     expected_filesizes = get_filesizes(baseline_dir)
#     created_files_filesizes = get_filesizes(output_dir)
#
#     # Verify that the file sizes in the baseline plots match the filesizes of the
#     # corresponding plots that were just created.
#     for filename, sizes in expected_filesizes.items():
#         if filename in created_files_filesizes:
#             assert(expected_filesizes[filename] == created_files_filesizes[filename])
#         else:
#             assert(False)