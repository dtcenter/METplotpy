import pytest
import os
from metplotpy.plots.contour import contour
from metcalcpy.compare_images import CompareImages


@pytest.fixture
def setup():
    # Cleanup the plotfile output file from any previous run
    cleanup()
    # Set up the METPLOTPY_BASE so that met_plot.py will correctly find
    # the config directory containing all the default config files.
    os.environ['METPLOTPY_BASE'] = "../../"

    # Invoke the command to generate a contour plot based on
    # the  config yaml files.

    contour.main("custom_contour.yaml")



def cleanup():
    # remove the previously created files
    try:
        path = os.getcwd()
        plot_file = 'contour.png'
        os.remove(os.path.join(path, plot_file))


    except OSError as e:
        # Typically, when files have already been removed or
        # don't exist.  Ignore.
        pass


@pytest.mark.parametrize("test_input, expected",
                         (["./contour_expected.png", True], ["./contour.png", True]
                        ))
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
    comparison = CompareImages('./contour_expected.png', './contour.png')
    assert comparison.mssim == 1
    cleanup()
