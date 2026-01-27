import os

import pytest

from metplotpy.plots.bar import bar


@pytest.mark.parametrize("input_yaml,expected_files", [
    ("custom_bar.yaml", ["bar.png", "intermed_files/bar.points1"]),
    ("bar_with_nones.yaml", ["bar_with_nones.png"]),
    ("threshold_bar.yaml", ["threshold_bar.png"]),
])
def test_bar(module_setup_env, remove_files, input_yaml, expected_files):
    """Checking that the plot file is getting created"""

    remove_files(os.environ['TEST_OUTPUT'], expected_files)

    bar.main(f"{os.environ['TEST_DIR']}/{input_yaml}")

    for expected_file in expected_files:
        assert os.path.isfile(f"{os.environ['TEST_OUTPUT']}/{expected_file}")

    if input_yaml == "custom_bar.yaml":
        check_custom_bar_nans()


def check_custom_bar_nans():
    """Checking that there are no NaNs in the data file.
     Check for NaNs in a file that is known to have NaNs to ensure check works as expected."""
    with open(f"{os.environ['TEST_OUTPUT']}/intermed_files/bar.points1", "r") as f:
        data = f.read()
    assert "NaN" not in data

    # Verify that the nan.points1 file does indeed trigger a "nans_found"
    with open(f"{os.environ['TEST_DIR']}/nan.points1", "r") as f:
        data = f.read()
    assert "NaN" in data
