import pytest
import os
from metplotpy.plots.wind_rose import wind_rose
from metcalcpy.compare_images import CompareImages


@pytest.fixture
def setup():
    # Cleanup the plotfile and point1 output file from any previous run
    cleanup()
    # Set up the METPLOTPY_BASE so that met_plot.py will correctly find
    # the config directory containing all the default config files.
    os.environ['METPLOTPY_BASE'] = "../../"
    custom_config_filename = "./wind_rose_custom.yaml"

    # Invoke the command to generate a Wind rose Diagram based on
    # a custom config file.
    wind_rose.main(custom_config_filename)


def cleanup():
    # remove the .png and .points files
    # from any previous runs
    try:
        path = os.getcwd()
        plot_file = 'wind_rose_custom.png'
        points_file_1 = 'point_stat_mpr.points1'
        os.remove(os.path.join(path, plot_file))
        os.remove(os.path.join(path, points_file_1))
    except OSError as e:
        # Typically when files have already been removed or
        # don't exist.  Ignore.
        pass


@pytest.mark.parametrize("test_input,expected",
                         (["wind_rose_expected.png", True], ["wind_rose_expected.points", True]))
def test_files_exist(setup, test_input, expected):
    '''
        Checking that the plot and data files are getting created
    '''
    assert os.path.isfile(test_input) == expected
    cleanup()



@pytest.mark.parametrize("test_input,expected",
                         (["./intermed_files/wind_rose_custom_points.png", True], ["./intermed_files/point_stat_mpr.points1", True]))
def test_points1_files_exist( test_input, expected):
    '''
        Checking that the plot file and points1 file are getting created where expected
        plot and point file are being saved in the intermed_files subdir
    '''
    os.environ['METPLOTPY_BASE'] = "../../"
    custom_config_filename = "wind_rose_custom_points.yaml"
    try:
        os.mkdir(os.path.join(os.getcwd(), './intermed_files'))
    except FileExistsError as e:
        pass

    # Invoke the command to generate a Wind Rose Diagram based on
    # a custom config file.
    wind_rose.main(custom_config_filename)

    assert os.path.isfile(test_input) == expected

    # remove the plot and points1 files that were created
    cleanup()
    try:
        path = os.getcwd()
        subdir = os.path.join(path, 'intermed_files')
        plot_file = 'wind_rose_custom_points.png'
        points_file_1 = 'point_stat_mpr.points1'
        os.remove(os.path.join(subdir, plot_file))
        os.remove(os.path.join(subdir, points_file_1))
        os.rmdir(subdir)
    except OSError as e:
        # Typically when files have already been removed or
        # don't exist.  Ignore.
        pass


@pytest.mark.parametrize("test_input,expected",
                         (["./intermed_files/wind_rose_points2.png", True],
                          ["./intermed_files/point_stat_mpr.points1", True]))
def test_points1_files_exist(test_input, expected):
    '''
        Checking that the plot file and points1 file are getting created where expected
        plot and point file are being saved in the intermed_files subdir. Verify that when
        no stat_file is specified, the point_stat_mpr.txt in the test dir is being used.
    '''
    os.environ['METPLOTPY_BASE'] = "../../"
    custom_config_filename = "wind_rose_custom2_points.yaml"
    try:
        os.mkdir(os.path.join(os.getcwd(), './intermed_files'))
    except FileExistsError as e:
        pass

    # Invoke the command to generate a Wind Rose Diagram based on
    # a custom config file.
    wind_rose.main(custom_config_filename)

    assert os.path.isfile(test_input) == expected

    # remove the plot and points1 files that were created
    cleanup()
    try:
        path = os.getcwd()
        subdir = os.path.join(path, 'intermed_files')
        plot_file = 'wind_rose_points2.png'
        points_file_1 = 'point_stat_mpr.points1'
        os.remove(os.path.join(subdir, plot_file))
        os.remove(os.path.join(subdir, points_file_1))
        os.rmdir(subdir)
    except OSError as e:
        # Typically when files have already been removed or
        # don't exist.  Ignore.
        pass
    
@pytest.mark.skip("unreliable sometimes fails due to differences in machines.")
def test_images_match(setup):
    '''
        Compare an expected plot with the
        newly created plot to verify that the plot hasn't
        changed in appearance.
    '''
    comparison = CompareImages('./wind_rose_expected.png', './wind_rose_custom.png')
    assert comparison.mssim == 1
    cleanup()
