
import pytest
import os
from metplotpy.plots.reliability_diagram import reliability as r
#from metcalcpy.compare_images import CompareImages

cwd = os.path.dirname(__file__)
CLEANUP_FILES = ['reliability.png', 'reliability.points1']


@pytest.fixture
def setup(setup_env, remove_files):
    # Cleanup the plotfile and point1 output file from any previous run
    remove_files(cwd, CLEANUP_FILES)
    setup_env(cwd)
    custom_config_filename = f"{cwd}/custom_reliability_use_defaults.yaml"

    # Invoke the command to generate a Performance Diagram based on
    # the test_custom_performance_diagram.yaml custom config file.
    r.main(custom_config_filename)


@pytest.mark.parametrize("test_input,expected",
                         ([CLEANUP_FILES[0], True], [CLEANUP_FILES[1], True]))
def test_files_exist(setup, test_input, expected, remove_files):
    '''
        Checking that the plot and data files are getting created
    '''
    assert os.path.isfile(f"{cwd}/{test_input}") == expected
    remove_files(cwd, CLEANUP_FILES)


@pytest.mark.skip("depends on machine on which this is run")
def test_images_match(setup, remove_files):
    '''
        Compare an expected plot with the
        newly created plot to verify that the plot hasn't
        changed in appearance.
    '''
    comparison = CompareImages(f'{cwd}/{CLEANUP_FILES[0]}', f'{cwd}/{CLEANUP_FILES[1]}')
    assert comparison.mssim == 1
    remove_files(cwd, CLEANUP_FILES)


@pytest.mark.parametrize("test_input,expected",
                         (["intermed_files/reliability.png", True], ["intermed_files/reliability.points1", True]))
def test_files_exist(setup_env, test_input, expected, remove_files):
    '''
        Checking that the plot and data files are getting created
    '''
    try:
        os.mkdir(os.path.join(cwd, 'intermed_files'))
    except FileExistsError:
        pass

    setup_env(cwd)
    custom_config_filename = f"{cwd}/custom_reliability_points1.yaml"
    r.main(custom_config_filename)

    assert os.path.isfile(f"{cwd}/{test_input}") == expected
    remove_files(cwd, ['intermed_files/reliability.png', 'intermed_files/reliability.points1'])
    try:
        os.rmdir(os.path.join(cwd, 'intermed_files'))
    except OSError:
        pass
