import pytest
import os
from metplotpy.plots.histogram import rank_hist

cwd = os.path.dirname(__file__)


@pytest.fixture
def setup(module_setup_env):
    cleanup()
    custom_config_filename = f"{cwd}/rank_hist.yaml"
    rank_hist.main(custom_config_filename)


def cleanup():
    # remove the rel_hist.png
    # from any previous runs
    try:
        plot_file = 'rank_hist.png'
        os.remove(os.path.join(os.environ['TEST_OUTPUT'], plot_file))
    except OSError:
        pass


def test_files_exist(setup):
    """
        Checking that the plot and data files are getting created
    """
    assert os.path.isfile(f"{os.environ['TEST_OUTPUT']}/rank_hist.png")
