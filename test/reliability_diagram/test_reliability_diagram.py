import pytest
import os
from metplotpy.plots.reliability_diagram import reliability as r

cwd = os.path.dirname(__file__)

@pytest.mark.parametrize("input_yaml, expected_files", [
    ("custom_reliability_diagram.yaml", ["custom_reliability_diagram.png"]),
    ("custom_reliability_points1.yaml", ["reliability_points1.png", "intermed_files/reliability.points1"]),
])
def test_files_exist(module_setup_env, remove_files, input_yaml, expected_files):
    """Checking that the plot and data files are getting created"""

    remove_files(os.environ['TEST_OUTPUT'], expected_files)

    r.main(f"{cwd}/{input_yaml}")

    for expected_file in expected_files:
        assert os.path.isfile(f"{os.environ['TEST_OUTPUT']}/{expected_file}")
