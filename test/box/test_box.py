import pytest
import os
from metplotpy.plots.box import box
#from metcalcpy.compare_images import CompareImages

cwd = os.path.dirname(__file__)
CLEANUP_FILES = ['box.png', 'box.points1']

@pytest.fixture
def setup(remove_files, module_setup_env):
    # Cleanup the plotfile and point1 output file from any previous run
    remove_files(os.path.join(os.environ['TEST_OUTPUT'], 'intermed_files'), ['box.points1'])
    remove_files(os.environ['TEST_OUTPUT'], ['box.png'])

    custom_config_filename = f"{cwd}/custom_box.yaml"
    box.main(custom_config_filename)


def test_custom_box(setup, remove_files):
    """
        Checking that the plot and data files are getting created
    """
    check_files = ("box.png", "intermed_files/box.points1")
    for check_file in check_files:
        assert os.path.isfile(f"{os.environ['TEST_OUTPUT']}/{check_file}")
