import os
import pytest

from metplotpy.plots.histogram_2d import histogram_2d as h2d

cwd = os.path.dirname(__file__)

# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# !!!!!!!!!  IMPORTANT !!!!!!
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# change the stat_input and plot_filename to explicitly point to this directory before
# running the test below because xarray cannot handle relative paths when reading in
# filenames
@pytest.mark.parametrize(
    "yaml_file, expected_output", [
        ("minimal_histogram_2d.yaml", "tmp_z2_p500.png"),
        ("custom_histogram_2d.yaml", "custom_tmp_z2_p500.png"),
    ]
)
def test_plot_exists(module_setup_env, yaml_file, expected_output, remove_files):
    """Checking that only the "defaults" plot file is getting created"""
    remove_files(os.environ['TEST_OUTPUT'], [expected_output])
    h2d.main(os.path.join(cwd, yaml_file))
    assert os.path.exists(f"{os.environ['TEST_OUTPUT']}/{expected_output}")
