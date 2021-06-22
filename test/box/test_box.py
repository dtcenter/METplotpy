# !!!IMPORTANT!!!
# activate conda environment in the testing subshell
# Replace blenny_363 with your METplus Python 3.6.3
# conda environment name
# !!!!!!!!

# !/usr/bin/env conda run -n blenny_363 python

import pytest
import os
from metplotpy.plots.box import box
from metcalcpy.compare_images import CompareImages


@pytest.fixture
def setup():
    # Cleanup the plotfile and point1 output file from any previous run
    cleanup()
    # Set up the METPLOTPY_BASE so that met_plot.py will correctly find
    # the config directory containing all the default config files.
    os.environ['METPLOTPY_BASE'] = "../../metplotpy"
    custom_config_filename = "custom_box.yaml"

    # Invoke the command to generate a Performance Diagram based on
    # the custom_performance_diagram.yaml custom config file.
    box.main(custom_config_filename)


def cleanup():
    # remove the box.png and .points files
    # from any previous runs
    try:
        path = os.getcwd()
        plot_file = 'box.png'
        points_file_1 = 'box.points1'
        os.remove(os.path.join(path, plot_file))
        os.remove(os.path.join(path, points_file_1))
    except OSError as e:
        # Typically when files have already been removed or
        # don't exist.  Ignore.
        pass


@pytest.mark.parametrize("test_input, expected",
                         (["./box_expected.png", True],["./box.points1", True]))
def test_files_exist(setup, test_input, expected):
    """
        Checking that the plot and data files are getting created
    """
    assert os.path.isfile(test_input) == expected
    cleanup()


def test_images_match(setup):
    """
        Compare an expected plot with the
        newly created plot to verify that the plot hasn't
        changed in appearance.
    """
    comparison = CompareImages('./box_expected.png', './box.png')
    assert comparison.mssim == 1
    cleanup()
