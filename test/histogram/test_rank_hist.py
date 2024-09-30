import pytest
import os
from metplotpy.plots.histogram import rank_hist
from metcalcpy.compare_images import CompareImages

cwd = os.path.dirname(__file__)


@pytest.fixture
def setup(setup_env):
    cleanup()
    setup_env(cwd)

    custom_config_filename = f"{cwd}/rank_hist.yaml"
    rank_hist.main(custom_config_filename)


def cleanup():
    # remove the rel_hist.png
    # from any previous runs
    try:
        plot_file = 'rank_hist.png'
        os.remove(os.path.join(cwd, plot_file))
    except OSError:
        pass


@pytest.mark.parametrize("test_input, expected",
                         (["rank_hist_expected.png", True],
                          ["rank_hist.png", True]))
def test_files_exist(setup, test_input, expected):
    """
        Checking that the plot and data files are getting created
    """
    assert os.path.isfile(f"{cwd}/{test_input}") == expected
    cleanup()


def test_images_match(setup):
    """
        Compare an expected plot with the
        newly created plot to verify that the plot hasn't
        changed in appearance.
    """
    comparison = CompareImages(f"{cwd}/rank_hist_expected.png",
                               f"{cwd}/rank_hist.png")
    assert comparison.mssim == 1
    cleanup()
