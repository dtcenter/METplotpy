import pytest
import os
from metplotpy.plots.revision_series import revision_series

cwd = os.path.dirname(__file__)

@pytest.mark.parametrize("input_yaml, expected_files", [
    ("custom_revision_series.yaml", ["revision_series.png", "intermed_files/revision_series.points1"]),
])
def test_files_exist(module_setup_env, remove_files, input_yaml, expected_files):
    """Checking that the plot and data files are getting created"""

    remove_files(os.environ['TEST_OUTPUT'], expected_files)

    revision_series.main(f"{cwd}/{input_yaml}")

    for expected_file in expected_files:
        assert os.path.isfile(f"{os.environ['TEST_OUTPUT']}/{expected_file}")
