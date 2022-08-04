import pytest
import os
from metplotpy.plots.eclv import eclv
from metcalcpy.compare_images import CompareImages


@pytest.fixture
def setup():
    # Cleanup the plotfile and point1 output file from any previous run
    cleanup()
    # Set up the METPLOTPY_BASE so that met_plot.py will correctly find
    # the config directory containing all the default config files.
    os.environ['METPLOTPY_BASE'] = "../../"

    # Invoke the command to generate a ECLV plots based on
    # the  config yaml files.

    eclv.main("custom_eclv_pct.yaml")
    eclv.main("custom_eclv.yaml")
    eclv.main("custom_eclv_ctc.yaml")


def cleanup():
    # remove the previously created files
    try:
        path = os.getcwd()
        plot_file = 'eclv_pct.png'
        os.remove(os.path.join(path, plot_file))
        plot_file = 'eclv.png'
        os.remove(os.path.join(path, plot_file))
        plot_file = 'eclv_ctc.png'
        os.remove(os.path.join(path, plot_file))

    except OSError as e:
        # Typically, when files have already been removed or
        # don't exist.  Ignore.
        pass


@pytest.mark.parametrize("test_input, expected",
                         (["./eclv_pct_expected.png", True], ["./eclv_pct.png", True],
                          ["./eclv_ctc_expected.png", True], ["./eclv_ctc.png", True],
                          ["./eclv_expected.png", True], ["./eclv.png", True]))
def test_files_exist(setup, test_input, expected):
    """
        Checking that the plot files are getting created
    """
    assert os.path.isfile(test_input) == expected
    cleanup()

@pytest.mark.skip("fails on linux hosts")
def test_images_match(setup):
    """
        Compare an expected plots with the
        newly created plots to verify that the plot hasn't
        changed in appearance.
    """
    comparison = CompareImages('./eclv_pct_expected.png', './eclv_pct.png')
    assert comparison.mssim == 1

    comparison = CompareImages('./eclv_expected.png', './eclv.png')
    assert comparison.mssim == 1

    comparison = CompareImages('./eclv_ctc_expected.png', './eclv_ctc.png')
    assert comparison.mssim == 1
    cleanup()
