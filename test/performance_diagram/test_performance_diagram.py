import os
import sys
sys.path.append("../../")
import yaml
import pytest
import plots.util as util
from plots.performance_diagram import performance_diagram as pd


from metcalcpy.compare_images import CompareImages
from plots.roc_diagram import roc_diagram as roc

@pytest.fixture
def setup():
    # Cleanup the plotfile and point1 output file from any previous run
    # cleanup()
    # Set up the METPLOTPY_BASE so that met_plot.py will correctly find
    # the config directory containing all the default config files.
    os.environ['METPLOTPY_BASE'] = "../../metplotpy"
    custom_config_filename = "./custom_performance_diagram.yaml"
    print("\n current directory: ", os.getcwd())
    print("\ncustom config file: ", custom_config_filename, '\n')

    # Invoke the command to generate a Performance Diagram based on
    # the custom_performance_diagram.yaml custom config file.
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
def test_files_exist(setup, test_input, expected_bool):
    '''
        Checking that only the plot file is getting created and the
         .point1 data file is not (dump_points_1 is 'False' in the test config file)
    '''
    assert os.path.isfile(test_input) == expected_bool
    cleanup()


def test_images_match(setup):
    '''
        Compare an expected plot with the
        newly created plot to verify that the plot hasn't
        changed in appearance.
    '''
    os.environ['METPLOTPY_BASE'] = "../../metplotpy"
    custom_config_filename = "./custom_performance_diagram.yaml"
    pd.main(custom_config_filename)

    path = os.getcwd()
    plot_file = 'performance_diagram_actual.png'
    actual_file = os.path.join(path, plot_file)
    comparison = CompareImages('./performance_diagram_expected.png',actual_file)
    assert comparison.mssim == 1
    cleanup()