import os
import pytest
#from metcalcpy.compare_images import CompareImages
from metplotpy.plots.ens_ss import ens_ss

cwd = os.path.dirname(__file__)

@pytest.fixture
def setup():
    # Cleanup the plotfile and point1 output file from any previous run
    cleanup()
    # Set up the METPLOTPY_BASE so that met_plot.py will correctly find
    # the config directory containing all the default config files.
    os.environ['METPLOTPY_BASE'] = f"{cwd}/../../"
    os.environ['TEST_DIR'] = cwd
    custom_config_filename = f"{cwd}/custom_ens_ss.yaml"

    # Invoke the command to generate a Bar plot based on
    # the custom_ens_ss.yaml custom config file.
    ens_ss.main(custom_config_filename)


def cleanup():
    # remove the .png and .points files
    # from any previous runs
    try:
        plot_file = 'ens_ss.png'
        points_file_1 = 'ens_ss.points1'
        os.remove(os.path.join(cwd, plot_file))
        os.remove(os.path.join(cwd, points_file_1))
    except OSError as er:
        # Typically when files have already been removed or
        # don't exist.  Ignore.
        pass


@pytest.mark.parametrize("test_input, expected",
                         ([f"{cwd}/ens_ss.png", True],[f"{cwd}/ens_ss.png", True],[f"{cwd}/ens_ss.points1", True]))
def test_files_exist( setup, test_input, expected):
    """
        Checking that the plot and data files are getting created
    """
    assert os.path.isfile(test_input) == expected
    cleanup()

@pytest.mark.skip("fails on linux hosts")
def test_images_match(setup):
    """
        Compare an expected plot with the
        newly created plot to verify that the plot hasn't
        changed in appearance.
    """
    comparison = CompareImages(f'{cwd}/ens_ss_expected.png', f'{cwd}/ens_ss.png')
    assert comparison.mssim == 1
    cleanup()


@pytest.mark.parametrize("test_input, expected",
                         ([f"{cwd}/intermed_files/ens_ss.png", True], [f"{cwd}/intermed_files/ens_ss.points1", True]))
def test_files_exist(test_input, expected):
    """
        Checking that the plot and data files are getting created
    """
    try:
        os.mkdir(os.path.join(cwd, 'intermed_files'))
    except FileExistsError as e:
        pass
    os.environ['METPLOTPY_BASE'] = f"{cwd}/../../"
    os.environ['TEST_DIR'] = cwd
    custom_config_filename = f"{cwd}/custom2_ens_ss.yaml"

    # Invoke the command to generate a Bar plot based on
    # the custom_ens_ss.yaml custom config file.
    ens_ss.main(custom_config_filename)
    assert os.path.isfile(test_input) == expected
    cleanup()
    try:
        subdir = os.path.join(cwd, "intermed_files")
        plot_file = 'ens_ss.png'
        points_file_1 = 'ens_ss.points1'
        os.remove(os.path.join(subdir, plot_file))
        os.remove(os.path.join(subdir, points_file_1))
        os.rmdir(subdir)
    except OSError as e:
        # Typically when files have already been removed or
        # don't exist.  Ignore.
        pass

