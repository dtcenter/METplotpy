import os
import pytest

from metplotpy.plots.performance_diagram import performance_diagram as performance_diagram

@pytest.mark.parametrize("input_yaml,expected_files", [
    ("custom_performance_diagram.yaml", [
        "performance_diagram_actual.png",
        "intermed_files/plot_20200317_151252.points1",
    ]),
])
def test_performance_diagram(module_setup_env, remove_files, input_yaml, expected_files):
    """Checking that the plot file is getting created"""

    remove_files(os.environ['TEST_OUTPUT'], expected_files)

    performance_diagram.main(f"{os.environ['TEST_DIR']}/{input_yaml}")

    for expected_file in expected_files:
        assert os.path.isfile(f"{os.environ['TEST_OUTPUT']}/{expected_file}")
