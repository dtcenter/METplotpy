import pytest
import os
from metplotpy.plots.wind_rose import wind_rose
from metcalcpy.compare_images import CompareImages

cwd = os.path.dirname(__file__)
CLEANUP_FILES = ['wind_rose_custom.png', 'point_stat_mpr.points1']

@pytest.fixture
def setup(remove_files, setup_env):
    # Cleanup the plotfile and point1 output file from any previous run
    remove_files(cwd, CLEANUP_FILES)
    setup_env(cwd)
    custom_config_filename = f"{cwd}/wind_rose_custom.yaml"

    # Invoke the command to generate a Wind rose Diagram based on
    # a custom config file.
    wind_rose.main(custom_config_filename)


def cleanup():
    # remove the .png and .points files
    # from any previous runs
    try:
        plot_file = 'wind_rose_custom.png'
        points_file_1 = 'point_stat_mpr.points1'
        os.remove(os.path.join(cwd, plot_file))
        os.remove(os.path.join(cwd, points_file_1))
    except OSError:
        pass


@pytest.mark.parametrize("test_input,expected",
                         (["wind_rose_expected.png", True], ["wind_rose_expected.points", True]))
def test_files_exist(setup, test_input, expected, remove_files):
    '''
        Checking that the plot and data files are getting created
    '''
    assert os.path.isfile(f"{cwd}/{test_input}") == expected
    remove_files(cwd, CLEANUP_FILES)


@pytest.mark.parametrize("test_input,expected",
                         (["intermed_files/wind_rose_custom_points.png", True], ["intermed_files/point_stat_mpr.points1", True]))
def test_points1_files_exist(setup_env, test_input, expected, remove_files):
    '''
        Checking that the plot file and points1 file are getting created where expected
        plot and point file are being saved in the intermed_files subdir
    '''
    setup_env(cwd)
    custom_config_filename = f"{cwd}/wind_rose_custom_points.yaml"
    try:
        os.mkdir(os.path.join(cwd, 'intermed_files'))
    except FileExistsError:
        pass

    # Invoke the command to generate a Wind Rose Diagram based on
    # a custom config file.
    wind_rose.main(custom_config_filename)

    assert os.path.isfile(f"{cwd}/{test_input}") == expected

    # remove the plot and points1 files that were created
    remove_files(cwd, CLEANUP_FILES)


@pytest.mark.parametrize("test_input,expected",
                         (["intermed_files/wind_rose_points2.png", True],
                          ["intermed_files/point_stat_mpr.points1", True]))
def test_points1_files_exist(setup_env, test_input, expected, remove_files):
    '''
        Checking that the plot file and points1 file are getting created where expected
        plot and point file are being saved in the intermed_files subdir. Verify that when
        no stat_file is specified, the point_stat_mpr.txt in the test dir is being used.
    '''
    setup_env(cwd)
    custom_config_filename = f"{cwd}/wind_rose_custom2_points.yaml"
    try:
        os.mkdir(os.path.join(cwd, 'intermed_files'))
    except FileExistsError:
        pass

    # Invoke the command to generate a Wind Rose Diagram based on
    # a custom config file.
    wind_rose.main(custom_config_filename)

    assert os.path.isfile(f"{cwd}/{test_input}") == expected

    # remove the plot and points1 files and intermed_files that were created
    remove_files(cwd, CLEANUP_FILES)


def test_images_match(setup, remove_files):
    '''
        Compare an expected plot with the
        newly created plot to verify that the plot hasn't
        changed in appearance.
    '''
    comparison = CompareImages(f'{cwd}/wind_rose_expected.png', f'{cwd}/wind_rose_custom.png')
    assert comparison.mssim == 1
    remove_files(cwd, CLEANUP_FILES)
