import pytest
import os
from metplotpy.plots.revision_box import revision_box

cwd = os.path.dirname(__file__)

def test_custom_revision_box(module_setup_env, remove_files):
    """Checking that the plot and data files are getting created"""
    expected_files = (
        'revision_box.png',
        'intermed_files/revision_box.points1'
    )

    remove_files(os.environ['TEST_OUTPUT'], expected_files)

    revision_box.main(f"{cwd}/custom_revision_box.yaml")

    for expected_file in expected_files:
        assert os.path.isfile(f"{os.environ['TEST_OUTPUT']}/{expected_file}")
