import pytest
import os
from metplotpy.plots.mpr_plot import mpr_plot
#from metcalcpy.compare_images import CompareImages

cwd = os.path.dirname(__file__)
CLEANUP_FILES = ['mpr_plots.png']


@pytest.fixture
def setup(setup_env, remove_files):
    # Cleanup the plotfile and point1 output file from any previous run
    remove_files(cwd, CLEANUP_FILES)
    setup_env(cwd)
    custom_config_filename = f"{cwd}/mpr_plot_custom.yaml"

    # Invoke the command to generate a Performance Diagram based on
    # the custom_performance_diagram.yaml custom config file.
    mpr_plot.main(custom_config_filename)


@pytest.mark.parametrize("test_input, expected",
                         (["mpr_plots.png", True], ["mpr_plots_expected.png", True]))
def test_files_exist(setup, test_input, expected, remove_files):
    """
        Checking that the plot and data files are getting created
    """
    assert os.path.isfile(f"{cwd}/{test_input}") == expected
    remove_files(cwd, CLEANUP_FILES)


@pytest.mark.skip("unreliable-sometimes fails due to differences between machines.")
def test_images_match(setup, remove_files):
    """
        Compare an expected plot with the
        newly created plot to verify that the plot hasn't
        changed in appearance.
    """
    comparison = CompareImages(f'{cwd}/mpr_plots_expected.png', f'{cwd}/mpr_plots.png')
    assert comparison.mssim == 1
    remove_files(cwd, CLEANUP_FILES)
