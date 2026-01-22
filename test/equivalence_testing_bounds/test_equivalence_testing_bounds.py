import pytest
import os
from metplotpy.plots.equivalence_testing_bounds import equivalence_testing_bounds as etb

cwd = os.path.dirname(__file__)

@pytest.fixture
def setup(remove_files, module_setup_env):
    # Cleanup the plotfile and point1 output file from any previous run
    remove_files(os.environ['TEST_OUTPUT'], 'equivalence_testing_bounds.png')
    remove_files(os.environ['TEST_OUTPUT'], 'intermed_files/equivalence_testing_bounds.points1')

    custom_config_filename = f"{cwd}/custom_equivalence_testing_bounds.yaml"
    etb.main(custom_config_filename)


def test_files_exist(setup):
    """Checking that the plot and data files are getting created"""
    assert os.path.isfile(f"{os.environ['TEST_OUTPUT']}/equivalence_testing_bounds.png")
    assert os.path.isfile(f"{os.environ['TEST_OUTPUT']}/intermed_files/equivalence_testing_bounds.points1")
