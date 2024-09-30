import pytest
import os
from metplotpy.plots.revision_box import revision_box
from metcalcpy.compare_images import CompareImages

cwd = os.path.dirname(__file__)
CLEANUP_FILES = ['revision_box.png', 'revision_box.points1']


@pytest.fixture
def setup(remove_files, setup_env):
    # Cleanup the plotfile and point1 output file from any previous run
    remove_files(cwd, CLEANUP_FILES)
    setup_env(cwd)
    custom_config_filename = f"{cwd}/custom_revision_box.yaml"

    # Invoke the command to generate a Revision Box plot based on
    # the custom_revision_box.yaml custom config file.
    revision_box.main(custom_config_filename)


@pytest.mark.parametrize("test_input, expected",
                         (["revision_box.png", True], ["revision_box.points1", True]))
def test_files_exist(setup, test_input, expected, remove_files):
    """
        Checking that the plot and data files are getting created
    """
    assert os.path.isfile(f"{cwd}/{test_input}") == expected
    remove_files(cwd, CLEANUP_FILES)


def test_images_match(setup, remove_files):
    """
        Compare an expected plot with the
        newly created plot to verify that the plot hasn't
        changed in appearance.
    """
    comparison = CompareImages(f'{cwd}/revision_box_expected.png', f'{cwd}/revision_box.png')
    assert comparison.mssim == 1
    remove_files(cwd, CLEANUP_FILES)


@pytest.mark.parametrize("test_input, expected",
                         (["intermed_files/revision_box.png", True], ["intermed_files/revision_box.points1", True]))
def test_files_exist(setup_env, test_input, expected, remove_files):
    """
        Checking that the plot and data files are getting created
    """
    setup_env(cwd)
    try:
        os.mkdir(os.path.join(cwd, 'intermed_files'))
    except FileExistsError:
        pass

    custom_config_filename = f"{cwd}/custom2_revision_box.yaml"

    # Invoke the command to generate a Bar plot based on
    # the custom_ens_ss.yaml custom config file.
    revision_box.main(custom_config_filename)
    assert os.path.isfile(f"{cwd}/{test_input}") == expected
    remove_files(cwd, CLEANUP_FILES)
