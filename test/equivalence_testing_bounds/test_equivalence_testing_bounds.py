import pytest
import os

from metplotpy.plots.equivalence_testing_bounds import equivalence_testing_bounds as etb

@pytest.mark.parametrize("input_yaml,expected_files", [
    ("custom_equivalence_testing_bounds.yaml", [
        "equivalence_testing_bounds.png",
        "intermed_files/equivalence_testing_bounds.points1",
    ]),
])
def test_equivalence_testing_bounds(module_setup_env, remove_files, input_yaml, expected_files):
    """Checking that the plot file is getting created"""

    remove_files(os.environ['TEST_OUTPUT'], expected_files)

    etb.main(f"{os.environ['TEST_DIR']}/{input_yaml}")

    for expected_file in expected_files:
        assert os.path.isfile(f"{os.environ['TEST_OUTPUT']}/{expected_file}")
