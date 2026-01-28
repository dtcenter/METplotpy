import pytest

import os

from metplotpy.plots.taylor_diagram import taylor_diagram as taylor_diagram

# Converts MatplotlibDeprecation warnings (which are DeprecationWarning) into errors as
# any DeprecationWarnings should be fixed as soon as possible
pytestmark = pytest.mark.filterwarnings("error::DeprecationWarning")


@pytest.mark.parametrize("input_yaml,expected_files", [
    ("test_pos_corr.yaml", ["test_pos_corr_plot.png"]),
    ("test_neg_and_pos_corr.yaml", ["test_neg_and_pos_corr_plot.png"]),
    ("taylor_diagram_custom.yaml", ["taylor_diagram_custom.png"]),
])
def test_taylor_diagram(module_setup_env, remove_files, input_yaml, expected_files):
    """Checking that the plot file is getting created"""

    remove_files(os.environ['TEST_OUTPUT'], expected_files)

    taylor_diagram.main(f"{os.environ['TEST_DIR']}/{input_yaml}")

    for expected_file in expected_files:
        assert os.path.isfile(f"{os.environ['TEST_OUTPUT']}/{expected_file}")
