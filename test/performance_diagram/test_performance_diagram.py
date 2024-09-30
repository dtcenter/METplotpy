import os
import pytest

from metplotpy.plots.performance_diagram import performance_diagram as pd
from metcalcpy.compare_images import CompareImages

cwd = os.path.dirname(__file__)

CLEANUP_FILES = ['performance_diagram_actual.png', 'plot_20200317_151252.points1']


@pytest.fixture
def setup(setup_env, remove_files):
    setup_env(cwd)
    # Cleanup the plotfile and point1 output file from any previous run
    remove_files(cwd, CLEANUP_FILES)
    custom_config_filename = f"{cwd}/custom_performance_diagram.yaml"
    # print("\n current directory: ", os.getcwd())
    # print("\ncustom config file: ", custom_config_filename, '\n')

    # Invoke the command to generate a Performance Diagram based on
    # the test_custom_performance_diagram.yaml custom config file.
    # Retrieve the contents of the custom config file to over-ride
    # or augment settings defined by the default config file.
    pd.main(custom_config_filename)


@pytest.mark.parametrize("test_input,expected_bool",(["performance_diagram_actual.png", True], ["plot_20200317_151252.points1", False]))
def test_plot_exists(setup, test_input, expected_bool, remove_files):
    '''
        Checking that only the plot file is getting created and the
         .point1 data file is not (dump_points_1 is 'False' in the test config file)
    '''

    assert os.path.isfile(f"{cwd}/{test_input}") == expected_bool
    remove_files(cwd, CLEANUP_FILES)

@pytest.mark.parametrize("test_input,expected_bool",(["./performance_diagram_actual_points1.png", True], ["./intermed_files/plot_20200317_151252.points1", True]))
def test_files_exist(setup_env, test_input, expected_bool, remove_files):
    '''
        Checking that only the plot file is getting created and the
         .point1 data file is not (dump_points_1 is 'False' in the test config file)
    '''
    setup_env(cwd)
    custom_config_filename = f"{cwd}/custom_performance_diagram_points1.yaml"
    try:
        os.mkdir(os.path.join(cwd, 'intermed_files'))
    except FileExistsError:
        pass

    # Invoke the command to generate a Performance Diagram based on
    # the test_custom_performance_diagram.yaml custom config file.
    # Retrieve the contents of the custom config file to over-ride
    # or augment settings defined by the default config file.
    pd.main(custom_config_filename)

    assert os.path.isfile(f"{cwd}/{test_input}") == expected_bool
    remove_files(cwd, ['performance_diagram_actual_points1.png', 'intermed_files/plot_20200317_151252.points1'])
    try:
        os.rmdir(os.path.join(cwd, 'intermed_files'))
    except OSError:
        pass


@pytest.mark.parametrize("test_input,expected_bool", (["performance_diagram_defaultpoints1.png", True], ["plot_20200317_151252.points1", True]))
def test_files_exist(setup_env, test_input, expected_bool, remove_files):
    '''
        Checking that only the plot file is getting created and the
         .point1 data file is not (dump_points_1 is 'False' in the test config file)
    '''
    setup_env(cwd)
    custom_config_filename = f"{cwd}/custom_performance_diagram_defaultpoints1.yaml"
    try:
       os.mkdir(os.path.join(cwd, 'intermed_files'))
    except FileExistsError:
        pass

    # Invoke the command to generate a Performance Diagram based on
    # the test_custom_performance_diagram.yaml custom config file.
    # Retrieve the contents of the custom config file to over-ride
    # or augment settings defined by the default config file.
    pd.main(custom_config_filename)

    assert os.path.isfile(f"{cwd}/{test_input}") == expected_bool
    remove_files(cwd, ['performance_diagram_defaultpoints1.png', 'plot_20200317_151252.points1'])
    try:
        os.rmdir(os.path.join(cwd, 'intermed_files'))
    except OSError:
        pass


def test_images_match(setup, remove_files):
    '''
        Compare an expected plot with the
        newly created plot to verify that the plot hasn't
        changed in appearance.
    '''
    custom_config_filename = f"{cwd}/custom_performance_diagram.yaml"
    pd.main(custom_config_filename)

    plot_file = 'performance_diagram_actual.png'
    actual_file = os.path.join(cwd, plot_file)
    comparison = CompareImages(f'{cwd}/performance_diagram_expected.png', actual_file)
    assert comparison.mssim == 1
    remove_files(cwd, CLEANUP_FILES)
