import pytest
import os
from metplotpy.plots.revision_series import revision_series
from metcalcpy.compare_images import CompareImages

cwd = os.path.dirname(__file__)
CLEANUP_FILES = ('revision_series.png', 'revision_series.points1')


@pytest.fixture
def setup(remove_files, setup_env):
    # Cleanup the plotfile and point1 output file from any previous run
    remove_files(cwd, CLEANUP_FILES)
    setup_env(cwd)
    custom_config_filename = f"{cwd}/custom_revision_series.yaml"

    # Invoke the command to generate a Revision Series plot based on
    # the custom_revision_series.yaml custom config file.
    revision_series.main(custom_config_filename)


@pytest.mark.parametrize("test_input, expected",
                         (["revision_series.png", True], ["revision_series.points1", True]))
def test_files_exist(setup, test_input, expected, remove_files):
    """
        Checking that the plot and data files are getting created
    """
    assert os.path.isfile(f"{cwd}/{test_input}") == expected
    remove_files(cwd, CLEANUP_FILES)


# @pytest.mark.skip("fails on linux hosts")
def test_images_match(setup, remove_files):
    """
        Compare an expected plot with the
        newly created plot to verify that the plot hasn't
        changed in appearance.
    """
    comparison = CompareImages('./revision_series_expected.png', './revision_series.png')
    assert comparison.mssim == 1
    remove_files(cwd, CLEANUP_FILES)


@pytest.mark.parametrize("test_input, expected",
                         (["intermed_files/revision_series.png", True],
                          ["intermed_files/revision_series.points1", True]))
def test_files_exist(setup_env, test_input, expected, remove_files):
    """
        Checking that the plot and data files are getting created
    """
    try:
        os.mkdir(os.path.join(cwd, 'intermed_files'))
    except FileExistsError:
        pass

    setup_env(cwd)
    custom_config_filename = f"{cwd}/custom2_revision_series.yaml"

    # Invoke the command to generate a Bar plot based on
    # the custom_ens_ss.yaml custom config file.
    revision_series.main(custom_config_filename)
    assert os.path.isfile(f"{cwd}/{test_input}") == expected
    remove_files(cwd, CLEANUP_FILES)

