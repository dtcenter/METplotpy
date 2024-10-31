import pytest
import os
from metplotpy.plots.box import box
#from metcalcpy.compare_images import CompareImages

cwd = os.path.dirname(__file__)
CLEANUP_FILES = ['box.png', 'box.points1']

@pytest.fixture
def setup(remove_files, setup_env):
    # Cleanup the plotfile and point1 output file from any previous run
    remove_files(cwd, CLEANUP_FILES)
    setup_env(cwd)
    custom_config_filename = f"{cwd}/custom_box.yaml"

    # Invoke the command to generate a Performance Diagram based on
    # the test_custom_performance_diagram.yaml custom config file.
    box.main(custom_config_filename)


@pytest.mark.parametrize("test_input, expected",
                         (["box.png", True], ["box.points1", True]))
def test_files_exist(setup, test_input, expected, remove_files):
    """
        Checking that the plot and data files are getting created
    """
    assert os.path.isfile(f"{cwd}/{test_input}") == expected
    remove_files(cwd, CLEANUP_FILES)


@pytest.mark.skip("fails on linux hosts")
def test_images_match(setup):
    """
        Compare an expected plot with the
        newly created plot to verify that the plot hasn't
        changed in appearance.
    """
    comparison = CompareImages(f'{cwd}/box_expected.png', f'{cwd}/box.png')
    assert comparison.mssim == 1
    remove_files(cwd, CLEANUP_FILES)


@pytest.mark.parametrize("test_input, expected",
                         (["box_expected.png", True], ["box_points1.png", True], ["intermed_files/box.points1", True]))
def test_points1_file_exist(setup_env, test_input, expected, remove_files):
    """
        Checking that the plot is created and points1 output files is created
        where specified in the custom_box_points1.yaml file
    """
    setup_env(cwd)
    custom_config_filename = f"{cwd}/custom_box_points1.yaml"
    try:
        os.mkdir(os.path.join(cwd, 'intermed_files'))
    except FileExistsError:
        pass

    # Invoke the command to generate a box plot based on
    # the custom_box_points1.yaml custom config file.
    box.main(custom_config_filename)
    assert os.path.isfile(f"{cwd}/{test_input}") == expected
    remove_files(cwd, ['box_points1.png'])


@pytest.mark.parametrize("test_input, expected",
                         (["box_defaultpoints1.png", True], ["box.points1", True]))
def test_defaultpoints1_file_exist(setup_env, test_input, expected, remove_files):
    """
        Checking that the plot is created and points1 output files is created
        in the default location (i.e. the current working dir, where the box.data file resides)
    """
    setup_env(cwd)
    custom_config_filename = f"{cwd}/custom_box_defaultpoints1.yaml"

    # Invoke the command to generate a box plot based on
    # the custom_box_defaultpoints1.yaml custom config file.
    box.main(custom_config_filename)
    assert os.path.isfile(f"{cwd}/{test_input}") == expected

    # remove the created plot and intermediate .points1 file
    remove_files(cwd, ['box_defaultpoints1.png', 'box.points1'])


def test_no_nans_in_points_file(setup, remove_files):
    """
        Checking that the points1 file does not contain NaN's
    """
    os.environ['METPLOTPY_BASE'] = f"{cwd}/../../"
    custom_config_filename = f"{cwd}/custom_box_defaultpoints1.yaml"

    # Invoke the command to generate a box plot based on
    # the custom_box_defaultpoints1.yaml custom config file.
    box.main(custom_config_filename)

    # Check for NaN's in the intermediate files, line.points1 and line.points2
    # Fail if there are any NaN's-this indicates something went wrong with the
    # line_series.py module's  _create_series_points() method.
    nans_found = False
    with open(f"{cwd}/box.points1", "r") as f:
        data = f.read()
        if "NaN" in data:
            nans_found = True

    assert not nans_found
    remove_files(cwd, CLEANUP_FILES)

    # Verify that the nan.points1 file does indeed trigger a "nans_found"
    with open(f"{cwd}/nan.points1", "r") as f:
        data = f.read()
        if "NaN" in data:
            nans_found = True

    # assert
    assert nans_found

    # remove the created plot and intermediate .points1 file
    remove_files(cwd, ['box_defaultpoints1.png', 'box.points1'])
