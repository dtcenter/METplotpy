import os
import sys
sys.path.append("../../")
import pytest
from plots.histogram_2d import histogram_2d as h2d
from metcalcpy.compare_images import CompareImages

@pytest.fixture
def setup():
    # Cleanup the plotfile and point1 output file from any previous run
    # cleanup()
    # Set up the METPLOTPY_BASE so that met_plot.py will correctly find
    # the config directory containing all the default config files.
    os.environ['METPLOTPY_BASE'] = "../../metplotpy"
    custom_config_filename = "./custom_histogram_2d.yaml"
    # print("\n current directory: ", os.getcwd())
    # print("\ncustom config file: ", custom_config_filename, '\n')

    # Invoke the command to generate a Performance Diagram based on
    # the test_custom_performance_diagram.yaml custom config file.
    # Retrieve the contents of the custom config file to over-ride
    # or augment settings defined by the default config file.
    # roc.main(custom_config_filename)
    h2d.main(custom_config_filename)


def cleanup():
    # remove the performance_diagram_expected.png and plot_20200317_151252.points1 files
    # from any previous runs
    try:
        path = os.getcwd()
        plot_file = '../../docs/Users_Guide/custom_tmp_z2_p500.png'

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
    cleanup()
