import os

import pytest

from metplotpy.plots.bar import bar

cwd = os.path.dirname(__file__)

@pytest.fixture
def setup(remove_files, module_setup_env):
    # Cleanup the plotfile and point1 output file from any previous run
    remove_files(os.path.join(os.environ['TEST_OUTPUT'], 'intermed_files'), ['bar.points1'])
    remove_files(os.environ['TEST_OUTPUT'], ['bar.png'])

    custom_config_filename = f"{cwd}/custom_bar.yaml"
    bar.main(custom_config_filename)


@pytest.fixture
def setup_nones(remove_files, module_setup_env):
    # Cleanup the plotfile from any previous run
    remove_files(os.environ['TEST_OUTPUT'], ['bar_with_nones.png'])
    custom_config_filename = f"{cwd}/bar_with_nones.yaml"

    bar.main(custom_config_filename)


def test_custom_bar(setup, remove_files):
    """Checking that the plot and data files are getting created and
     that there are no NaNs in the data file. Check for NaNs in a file that
     is known to have NaNs to ensure check works as expected."""
    check_files = ("bar.png", "intermed_files/bar.points1")
    for check_file in check_files:
        assert os.path.isfile(f"{os.environ['TEST_OUTPUT']}/{check_file}")

    with open(f"{os.environ['TEST_OUTPUT']}/intermed_files/bar.points1", "r") as f:
        data = f.read()
    assert "NaN" not in data

    # Verify that the nan.points1 file does indeed trigger a "nans_found"
    with open(f"{cwd}/nan.points1", "r") as f:
        data = f.read()
    assert "NaN" in data


def test_bar_with_nones(setup_nones):
    """
        Compare an expected plot with the
        newly created plot to verify that the plot hasn't
        changed in appearance.
    """
    assert os.path.isfile(f"{os.environ['TEST_OUTPUT']}/bar_with_nones.png")


def test_threshold_plotting(module_setup_env, remove_files):
    """Verify that the bar plot using data with thresholds is correct."""
    # Cleanup the plotfile and point1 output file from any previous run
    remove_files(os.environ['TEST_OUTPUT'], ['threshold_bar.png'])

    custom_config_filename = f"{cwd}/threshold_bar.yaml"
    bar.main(custom_config_filename)
    assert os.path.isfile(f"{os.environ['TEST_OUTPUT']}/threshold_bar.png")
