import os
import pytest

from metplotpy.plots.ens_ss import ens_ss


@pytest.mark.parametrize("input_yaml,expected_files", [
    ("custom_ens_ss.yaml", ["ens_ss.png", "intermed_files/ens_ss.points1"]),
])
def test_ens_ss(module_setup_env, remove_files, input_yaml, expected_files):
    """Checking that the plot file is getting created"""

    remove_files(os.environ['TEST_OUTPUT'], expected_files)

    ens_ss.main(f"{os.environ['TEST_DIR']}/{input_yaml}")

    for expected_file in expected_files:
        assert os.path.isfile(f"{os.environ['TEST_OUTPUT']}/{expected_file}")
