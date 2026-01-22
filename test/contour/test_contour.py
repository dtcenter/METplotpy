import pytest
import os
from metplotpy.plots.contour import contour

cwd = os.path.dirname(__file__)

@pytest.fixture
def setup(module_setup_env):
    # Cleanup the plotfile output file from any previous run
    cleanup()

    contour.main(f"{cwd}/custom_contour.yaml")


def cleanup():
    # remove the previously created files
    try:
        plot_file = 'contour.png'
        os.remove(os.path.join(os.environ['TEST_OUTPUT'], plot_file))
    except OSError:
        pass


def test_files_exist(setup):
    """Checking that the plot files are getting created"""
    assert os.path.isfile(os.path.join(os.environ['TEST_OUTPUT'], 'contour.png'))
