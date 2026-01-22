import os
import pytest

from metplotpy.plots.ens_ss import ens_ss

cwd = os.path.dirname(__file__)

@pytest.fixture
def setup(module_setup_env):
    # Cleanup the plotfile and point1 output file from any previous run
    cleanup()

    custom_config_filename = f"{cwd}/custom_ens_ss.yaml"
    ens_ss.main(custom_config_filename)


def cleanup():
    # remove the .png and .points files
    # from any previous runs
    try:
        plot_file = 'ens_ss.png'
        points_file_1 = 'intermed_files/ens_ss.points1'
        os.remove(os.path.join(os.environ['TEST_OUTPUT'], plot_file))
        os.remove(os.path.join(os.environ['TEST_OUTPUT'], points_file_1))
    except OSError:
        pass


def test_custom_ens_ss(setup):
    """Checking that the plot and data files are getting created"""
    assert os.path.isfile(os.path.join(os.environ['TEST_OUTPUT'], 'ens_ss.png'))
    assert os.path.isfile(os.path.join(os.environ['TEST_OUTPUT'], 'intermed_files', 'ens_ss.points1'))
