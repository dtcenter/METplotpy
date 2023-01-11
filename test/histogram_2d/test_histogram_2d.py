import os
import sys
import pytest

from metplotpy.plots.histogram_2d import histogram_2d as h2d
#from metcalcpy.compare_images import CompareImages

@pytest.fixture
def setup():
    # Cleanup the plotfile and point1 output file from any previous run
    # cleanup()
    # Set up the METPLOTPY_BASE so that met_plot.py will correctly find
    # the config directory containing all the default config files.
    os.environ['METPLOTPY_BASE'] = "../../"
    custom_config_filename = "./minimal_histogram_2d.yaml"
    # print("\n current directory: ", os.getcwd())
    # print("\ncustom config file: ", custom_config_filename, '\n')

    # Invoke the command to generate a histogram_2d plot based on
    # the settings in the "defaults" config file.
    h2d.main(custom_config_filename)


#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# !!!!!!!!!  IMPORTANT !!!!!!
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# change the stat_input and plot_filename to explicitly point to this directory before
# running the test below because xarray cannot handle relative paths when reading in filenames
# def test_plot_exists(setup):
#     '''
#         Checking that only the "defaults" plot file is getting created
#
#     '''
#     test_input = "./tmp_z2_p500.png"
#     assert os.path.exists(test_input)
#     # cleanup
#     try:
#         path = os.getcwd()
#         plot_file = 'tmp_z2_p500.png'
#         os.remove(os.path.join(path, plot_file))
#     except OSError as e:
#         # Typically when files have already been removed or
#         # don't exist.  Ignore.
#         pass

