import pytest
import os
from metplotpy.plots.box import box


@pytest.mark.parametrize("input_yaml,expected_files", [
    ("custom_box.yaml", ["box.png", "intermed_files/box.points1"]),
])
def test_box(module_setup_env, remove_files, input_yaml, expected_files):
    """Checking that the plot file is getting created"""

    remove_files(os.environ['TEST_OUTPUT'], expected_files)

    box.main(f"{os.environ['TEST_DIR']}/{input_yaml}")

    for expected_file in expected_files:
        assert os.path.isfile(f"{os.environ['TEST_OUTPUT']}/{expected_file}")
