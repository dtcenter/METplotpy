import pytest
import os
from metplotpy.plots.eclv import eclv

cwd = os.path.dirname(__file__)


def cleanup(plot_file):
    # remove the previously created files
    try:
        os.remove(os.path.join(os.environ['TEST_OUTPUT'], plot_file))
    except OSError:
        pass


@pytest.mark.parametrize(
    "yaml_file, expected_output", [
        ("custom_eclv.yaml", "eclv.png"),
        ("custom_eclv_pct.yaml", "eclv_pct.png"),
        ("custom_eclv_ctc.yaml", "eclv_ctc.png"),
    ]
)
def test_files_exist(module_setup_env, yaml_file, expected_output):
    """
        Checking that the plot files are getting created
    """
    cleanup(expected_output)
    eclv.main(f"{cwd}/{yaml_file}")
    assert os.path.isfile(os.path.join(os.environ['TEST_OUTPUT'], expected_output))
