import pytest

import os

from metplotpy.plots.skew_t import skew_t as skew_t

def test_skew_t(module_setup_env):
    expected_times = {
        '2023010100': range(0, 61, 6),
        '2023010106': range(0, 49, 6),
    }
    expected_files = []
    for init, leads in expected_times.items():
        for lead in leads:
            expected_files.append(f'ssh052023_avno_doper_{init}_diag_{lead}_hr.png')

    custom_config_filename = os.path.join(os.environ['TEST_DIR'], "test_skew_t.yaml")
    skew_t.main(custom_config_filename)

    # Verify that files for the ssh052023 data exists for
    # the 0, 6, 12, 18, 24, 30, 42, 48, 54, and 60 hour data.
    # Some of these data files have incomplete data so check for the expected hour plots.

    file_ext = '.png'
    files_of_interest = []
    for root, _, files in os.walk(os.environ['TEST_OUTPUT']):
        for item in files:
            if item.endswith(file_ext):
                full_file = os.path.join(root, item)
                base_file = os.path.basename(full_file)
                files_of_interest.append(base_file)

    assert len(expected_files) == len(files_of_interest)
    for expected_file in expected_files:
        assert expected_file in files_of_interest
