import pytest
import os
from metplotpy.plots.revision_series import revision_series
from metcalcpy.compare_images import CompareImages


@pytest.fixture
def setup():
    # Cleanup the plotfile and point1 output file from any previous run
    cleanup()
    # Set up the METPLOTPY_BASE so that met_plot.py will correctly find
    # the config directory containing all the default config files.
    os.environ['METPLOTPY_BASE'] = "../../"
    custom_config_filename = "custom_revision_series.yaml"

    # Invoke the command to generate a Revision Series plot based on
    # the custom_revision_series.yaml custom config file.
    revision_series.main(custom_config_filename)


def cleanup():
    # remove the .png and .points files
    # from any previous runs
    try:
        path = os.getcwd()
        plot_file = 'revision_series.png'
        points_file_1 = 'revision_series.points1'
        os.remove(os.path.join(path, plot_file))
        os.remove(os.path.join(path, points_file_1))
    except OSError as er:
        # Typically when files have already been removed or
        # don't exist.  Ignore.
        pass


@pytest.mark.parametrize("test_input, expected",
                         (["./revision_series.png", True],["./revision_series.points1", True]))
def test_files_exist( setup, test_input, expected):
    """
        Checking that the plot and data files are getting created
    """
    assert os.path.isfile(test_input) == expected
    cleanup()

#@pytest.mark.skip("fails on linux hosts")
def test_images_match(setup):
    """
        Compare an expected plot with the
        newly created plot to verify that the plot hasn't
        changed in appearance.
    """
    comparison = CompareImages('./revision_series_expected.png', './revision_series.png')
    assert comparison.mssim == 1
    cleanup()


@pytest.mark.parametrize("test_input, expected",
                         (["./intermed_files/revision_series.png", True], ["./intermed_files/revision_series.points1", True]))
def test_files_exist(test_input, expected):
    """
        Checking that the plot and data files are getting created
    """
    try:
        os.mkdir(os.path.join(os.getcwd(), './intermed_files'))
    except FileExistsError as e:
        pass
    os.environ['METPLOTPY_BASE'] = "../../"
    custom_config_filename = "custom2_revision_series.yaml"

    # Invoke the command to generate a Bar plot based on
    # the custom_ens_ss.yaml custom config file.
    revision_series.main(custom_config_filename)
    assert os.path.isfile(test_input) == expected
    cleanup()
    try:
        path = os.getcwd()
        subdir = os.path.join(path, "./intermed_files")
        plot_file = 'revision_series.png'
        points_file_1 = 'revision_series.points1'
        os.remove(os.path.join(subdir, plot_file))
        os.remove(os.path.join(subdir, points_file_1))
        os.rmdir(subdir)
    except OSError as e:
        # Typically when files have already been removed or
        # don't exist.  Ignore.
        pass

