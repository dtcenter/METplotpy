import pytest
import os
from metplotpy.plots.equivalence_testing_bounds import equivalence_testing_bounds as etb
from metcalcpy.compare_images import CompareImages

cwd = os.path.dirname(__file__)
CLEANUP_FILES = ['equivalence_testing_bounds.png', 'equivalence_testing_bounds.points1']

@pytest.fixture
def setup(remove_files, setup_env):
    # Cleanup the plotfile and point1 output file from any previous run
    remove_files(cwd, CLEANUP_FILES)
    setup_env(cwd)
    custom_config_filename = f"{cwd}/custom_equivalence_testing_bounds.yaml"

    # Invoke the command to generate an equivalence testing boundary plot based on
    # the custom config file.
    etb.main(custom_config_filename)


@pytest.mark.parametrize("test_input,expected",
                         (["equivalence_testing_bounds.png", True],
                          ["equivalence_testing_bounds.points1", True]))
def test_files_exist(setup, test_input, expected, remove_files):
    '''
        Checking that the plot and data files are getting created
    '''
    assert os.path.isfile(f"{cwd}/{test_input}") == expected
    remove_files(cwd, CLEANUP_FILES)


def test_images_match(setup, remove_files):
    '''
        Compare an expected plot with the
        newly created plot to verify that the plot hasn't
        changed in appearance.
    '''
    plot_file = 'equivalence_testing_bounds.png'
    actual_file = os.path.join(cwd, plot_file)
    comparison = CompareImages(f'{cwd}/equivalence_testing_bounds_expected.png', actual_file)
    assert comparison.mssim == 1
    remove_files(cwd, CLEANUP_FILES)


@pytest.mark.parametrize("test_input,expected",
                         (["intermed_files/equivalence_testing_bounds.png", True],
                          ["intermed_files/equivalence_testing_bounds.points1", True]))
def test_files_exist(setup_env, test_input, expected, remove_files):
    '''
        Checking that the plot and data files are getting created
    '''

    intermed_dir = os.path.join(cwd, 'intermed_files')
    try:
        os.mkdir(intermed_dir)
    except FileExistsError:
        pass

    setup_env(cwd)
    custom_config_filename = f"{cwd}/custom_equivalence_testing_bounds2.yaml"

    # Invoke the command to generate an equivalence testing boundary plot based on
    # the custom config file.
    etb.main(custom_config_filename)

    assert os.path.isfile(f"{cwd}/{test_input}") == expected
    remove_files(cwd, ['intermed_files/equivalence_testing_bounds.png',
                       'intermed_files/equivalence_testing_bounds.points1',
                       'intermed_files/equivalence_testing_bounds.html'])
    try:
        os.rmdir(intermed_dir)
    except OSError:
        pass
