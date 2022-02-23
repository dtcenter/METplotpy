import os
import pytest

from metplotpy.plots.performance_diagram import performance_diagram as pd
from metcalcpy.compare_images import CompareImages

@pytest.fixture
def setup():
    # Cleanup the plotfile and point1 output file from any previous run
    # cleanup()
    # Set up the METPLOTPY_BASE so that met_plot.py will correctly find
    # the config directory containing all the default config files.
    os.environ['METPLOTPY_BASE'] = "../../"
    custom_config_filename = "./custom_performance_diagram.yaml"
    # print("\n current directory: ", os.getcwd())
    # print("\ncustom config file: ", custom_config_filename, '\n')

    # Invoke the command to generate a Performance Diagram based on
    # the test_custom_performance_diagram.yaml custom config file.
    # Retrieve the contents of the custom config file to over-ride
    # or augment settings defined by the default config file.
    # roc.main(custom_config_filename)
    pd.main(custom_config_filename)


def cleanup():
    # remove the performance_diagram_expected.png and plot_20200317_151252.points1 files
    # from any previous runs
    try:
        path = os.getcwd()
        plot_file = 'performance_diagram_actual.png'
        points_file = 'plot_20200317_151252.points1'
        os.remove(os.path.join(path, plot_file))
        os.remove(os.path.join(path, points_file))
    except OSError as e:
        # Typically when files have already been removed or
        # don't exist.  Ignore.
        pass


@pytest.mark.parametrize("test_input,expected_bool",(["./performance_diagram_actual.png", True], ["./plot_20200317_151252.points1", False]))
def test_plot_exists(setup, test_input, expected_bool):
    '''
        Checking that only the plot file is getting created and the
         .point1 data file is not (dump_points_1 is 'False' in the test config file)
    '''

    assert os.path.isfile(test_input) == expected_bool
    # cleanup()

@pytest.mark.parametrize("test_input,expected_bool",(["./performance_diagram_actual_points1.png", True], ["./intermed_files/plot_20200317_151252.points1", True]))
def test_files_exist(test_input, expected_bool):
    '''
        Checking that only the plot file is getting created and the
         .point1 data file is not (dump_points_1 is 'False' in the test config file)
    '''

    os.environ['METPLOTPY_BASE'] = "../../"
    custom_config_filename = "./custom_performance_diagram_points1.yaml"
    try:
       os.mkdir(os.path.join(os.getcwd(), 'intermed_files'))
    except FileExistsError as e:
        pass

    # Invoke the command to generate a Performance Diagram based on
    # the test_custom_performance_diagram.yaml custom config file.
    # Retrieve the contents of the custom config file to over-ride
    # or augment settings defined by the default config file.
    # roc.main(custom_config_filename)
    pd.main(custom_config_filename)

    assert os.path.isfile(test_input) == expected_bool
    try:
        path = os.getcwd()
        plot_file = 'performance_diagram_actual_points1.png'
        points_file = './intermed_files/plot_20200317_151252.points1'
        os.remove(os.path.join(path, plot_file))
        os.remove(os.path.join(path, points_file))
        os.rmdir(os.path.join(path, './intermed_files'))
    except OSError as e:
        # Typically when files have already been removed or
        # don't exist.  Ignore.
        pass


@pytest.mark.parametrize("test_input,expected_bool",(["./performance_diagram_defaultpoints1.png", True], ["./plot_20200317_151252.points1", True]))
def test_files_exist(test_input, expected_bool):
    '''
        Checking that only the plot file is getting created and the
         .point1 data file is not (dump_points_1 is 'False' in the test config file)
    '''

    os.environ['METPLOTPY_BASE'] = "../../"
    custom_config_filename = "./custom_performance_diagram_defaultpoints1.yaml"
    try:
       os.mkdir(os.path.join(os.getcwd(), 'intermed_files'))
    except FileExistsError as e:
        pass

    # Invoke the command to generate a Performance Diagram based on
    # the test_custom_performance_diagram.yaml custom config file.
    # Retrieve the contents of the custom config file to over-ride
    # or augment settings defined by the default config file.
    # roc.main(custom_config_filename)
    pd.main(custom_config_filename)

    assert os.path.isfile(test_input) == expected_bool
    try:
        path = os.getcwd()
        plot_file = 'performance_diagram_defaultpoints1.png'
        points_file = 'plot_20200317_151252.points1'
        os.remove(os.path.join(path, plot_file))
        os.remove(os.path.join(path, points_file))
        os.rmdir(os.path.join(path,'./intermed_files'))
    except OSError as e:
        # Typically when files have already been removed or
        # don't exist.  Ignore.
        pass


@pytest.mark.skip()
def test_images_match(setup):
    '''
        Compare an expected plot with the
        newly created plot to verify that the plot hasn't
        changed in appearance.
    '''
    os.environ['METPLOTPY_BASE'] = "../../"
    custom_config_filename = "./custom_performance_diagram.yaml"
    pd.main(custom_config_filename)

    path = os.getcwd()
    plot_file = 'performance_diagram_actual.png'
    actual_file = os.path.join(path, plot_file)
    comparison = CompareImages('./performance_diagram_expected.png',actual_file)
    assert comparison.mssim == 1
    cleanup()
