import pytest

import os

from metplotpy.plots.mpr_plot import mpr_plot


def test_files_exist(module_setup_env, remove_files):
    """Checking that the plot and data files are getting created"""
    expected_file = "mpr_plots.png"

    remove_files(os.environ['TEST_OUTPUT'], expected_file)

    mpr_plot.main(f"{os.environ['TEST_DIR']}/mpr_plot_custom.yaml")

    assert os.path.isfile(f"{os.environ['TEST_OUTPUT']}/{expected_file}")
