import pytest
import os
from metplotpy.plots.histogram import rel_hist

cwd = os.path.dirname(__file__)


@pytest.fixture
def setup(module_setup_env):
    # Cleanup the plotfile  output file from any previous run
    cleanup()
    custom_config_filename = f"{cwd}/rel_hist.yaml"
    rel_hist.main(custom_config_filename)


def cleanup():
    # remove the rel_hist.png
    # from any previous runs
    try:
        plot_file = 'rel_hist.png'
        os.remove(os.path.join(os.environ['TEST_OUTPUT'], plot_file))
    except OSError:
        pass


def test_files_exist(setup):
    """
        Checking that the plot and data files are getting created
    """
    assert os.path.isfile(f"{os.environ['TEST_OUTPUT']}/rel_hist.png")
