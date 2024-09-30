import os
import pytest

from metplotpy.plots.histogram_2d import histogram_2d as h2d

cwd = os.path.dirname(__file__)


@pytest.fixture
def setup(setup_env):
    # Cleanup the plotfile and point1 output file from any previous run
    # cleanup()
    setup_env(cwd)
    custom_config_filename = f"{cwd}/minimal_histogram_2d.yaml"
    # print("\n current directory: ", os.getcwd())
    # print("\ncustom config file: ", custom_config_filename, '\n')

    # Invoke the command to generate a histogram_2d plot based on
    # the settings in the "defaults" config file.
    h2d.main(custom_config_filename)


# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# !!!!!!!!!  IMPORTANT !!!!!!
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# change the stat_input and plot_filename to explicitly point to this directory before
# running the test below because xarray cannot handle relative paths when reading in
# filenames
def test_plot_exists(setup, remove_files):
    '''
        Checking that only the "defaults" plot file is getting created

    '''
    test_input = "tmp_z2_p500.png"
    assert os.path.exists(f"{cwd}/{test_input}")
    remove_files(cwd, ['tmp_z2_p500.png'])
