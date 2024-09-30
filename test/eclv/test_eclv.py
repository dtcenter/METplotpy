import pytest
import os
from metplotpy.plots.eclv import eclv
from metcalcpy.compare_images import CompareImages

cwd = os.path.dirname(__file__)

@pytest.fixture
def setup():
    # Cleanup the plotfile and point1 output file from any previous run
    cleanup()
    # Set up the METPLOTPY_BASE so that met_plot.py will correctly find
    # the config directory containing all the default config files.
    os.environ['METPLOTPY_BASE'] = f"{cwd}/../../"
    os.environ['TEST_DIR'] = cwd

    # Invoke the command to generate a ECLV plots based on
    # the  config yaml files.

    eclv.main(f"{cwd}/custom_eclv_pct.yaml")
    eclv.main(f"{cwd}/custom_eclv.yaml")
    eclv.main(f"{cwd}/custom_eclv_ctc.yaml")


def cleanup():
    # remove the previously created files
    try:
        plot_file = 'eclv_pct.png'
        os.remove(os.path.join(cwd, plot_file))
        plot_file = 'eclv.png'
        os.remove(os.path.join(cwd, plot_file))
        plot_file = 'eclv_ctc.png'
        os.remove(os.path.join(cwd, plot_file))

    except OSError as e:
        # Typically, when files have already been removed or
        # don't exist.  Ignore.
        pass


@pytest.mark.parametrize("test_input, expected",
                         ([f"{cwd}/eclv_pct_expected.png", True], [f"{cwd}/eclv_pct.png", True],
                          [f"{cwd}/eclv_ctc_expected.png", True], [f"{cwd}/eclv_ctc.png", True],
                          [f"{cwd}/eclv_expected.png", True], [f"{cwd}/eclv.png", True]))
def test_files_exist(setup, test_input, expected):
    """
        Checking that the plot files are getting created
    """
    assert os.path.isfile(test_input) == expected
    cleanup()

def test_images_match(setup):
    """
        Compare an expected plots with the
        newly created plots to verify that the plot hasn't
        changed in appearance.
    """
    comparison = CompareImages(f'{cwd}/eclv_pct_expected.png', './eclv_pct.png')
    assert comparison.mssim == 1

    comparison = CompareImages(f'{cwd}/eclv_expected.png', './eclv.png')
    assert comparison.mssim == 1

    comparison = CompareImages(f'{cwd}/eclv_ctc_expected.png', './eclv_ctc.png')
    assert comparison.mssim == 1
    cleanup()
