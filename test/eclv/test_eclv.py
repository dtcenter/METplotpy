import pytest
import os
from metplotpy.plots.eclv import eclv


@pytest.mark.parametrize(
    "yaml_file, expected_output", [
        ("custom_eclv.yaml", "eclv.png"),
        ("custom_eclv_pct.yaml", "eclv_pct.png"),
        ("custom_eclv_ctc.yaml", "eclv_ctc.png"),
    ]
)
def test_files_exist(module_setup_env, remove_files, yaml_file, expected_output):
    """
        Checking that the plot files are getting created
    """
    remove_files(os.environ['TEST_OUTPUT'], expected_output)
    eclv.main(f"{os.environ['TEST_DIR']}/{yaml_file}")
    assert os.path.isfile(os.path.join(os.environ['TEST_OUTPUT'], expected_output))
