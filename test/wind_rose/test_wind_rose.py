import pytest
import os
from metplotpy.plots.wind_rose import wind_rose

cwd = os.path.dirname(__file__)

@pytest.mark.parametrize("input_yaml,expected_files", [
    ("wind_rose_custom.yaml", [
        "wind_rose_custom.png",
        "custom/point_stat_mpr.points1",
    ]),
    ("wind_rose_custom_points.yaml", [
        "wind_rose_custom_points.png",
        "custom_points/point_stat_mpr.points1",
    ]),
    ("minimal_wind_rose.yaml", [
        "wind_rose_minimal.png",
        "minimal/point_stat_mpr.points1",
    ]),
])
def test_wind_rose(module_setup_env, remove_files, input_yaml, expected_files):
    """Checking that the plots are being created"""

    remove_files(os.environ['TEST_OUTPUT'], expected_files)

    wind_rose.main(f"{cwd}/{input_yaml}")

    for expected_file in expected_files:
        assert os.path.isfile(f"{os.environ['TEST_OUTPUT']}/{expected_file}")
