import pytest
import os
from metplotpy.plots.histogram import rel_hist
#from metcalcpy.compare_images import CompareImages

cwd = os.path.dirname(__file__)


@pytest.fixture
def setup(setup_env):
    # Cleanup the plotfile  output file from any previous run
    cleanup()
    setup_env(cwd)
    custom_config_filename = f"{cwd}/rel_hist.yaml"

    # Invoke the command to generate a histogram based on
    # the rel_hist.yaml custom config file.
    rel_hist.main(custom_config_filename)


def cleanup():
    # remove the rel_hist.png
    # from any previous runs
    try:
        plot_file = 'rel_hist.png'
        os.remove(os.path.join(cwd, plot_file))
    except OSError:
        pass


@pytest.mark.parametrize("test_input, expected",
                         (["rel_hist_expected.png", True],
                          ["rel_hist.png", True]))
def test_files_exist(setup, test_input, expected):
    """
        Checking that the plot and data files are getting created
    """
    assert os.path.isfile(f"{cwd}/{test_input}") == expected
    cleanup()


@pytest.mark.skip("Image comparisons fail in Github Actions checks.")
def test_images_match(setup):
    """
        Compare an expected plot with the
        newly created plot to verify that the plot hasn't
        changed in appearance.
    """
    comparison = CompareImages(f"{cwd}/rel_hist_expected.png",
                               f"{cwd}/rel_hist.png")
    assert comparison.mssim == 1
    cleanup()
