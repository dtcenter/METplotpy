import pytest
import os
from metplotpy.plots.line import line as l

cwd = os.path.dirname(__file__)


def test_custom_line_groups(module_setup_env, remove_files):
    """Checking that the plot and data files are getting created"""
    expected_files = (
        "line_groups.png",
        "line_groups.points1",
        "line_groups.points2",
        "line_groups.html",
    )

    remove_files(os.environ['TEST_OUTPUT'], expected_files)

    l.main(f"{cwd}/custom_line_groups.yaml")

    for expected_file in expected_files:
        assert os.path.isfile(os.path.join(os.environ['TEST_OUTPUT'], expected_file))


def test_custom_line_groups2(module_setup_env, remove_files):
    """Checking that the plot and data files are getting created"""
    expected_files = (
        "line_groups2.png",
        "intermed_files/line_groups.points1",
        "intermed_files/line_groups.points2",
    )

    remove_files(os.environ['TEST_OUTPUT'], expected_files)

    l.main(f"{cwd}/custom_line_groups2.yaml")

    for expected_file in expected_files:
        assert os.path.isfile(os.path.join(os.environ['TEST_OUTPUT'], expected_file))
