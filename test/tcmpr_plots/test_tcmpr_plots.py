import pytest
import os

import metplotpy.plots.tcmpr_plots.tcmpr as tcmpr

cwd = os.path.dirname(__file__)

@pytest.mark.parametrize("input_yaml,expected_files", [
    ("tcmpr_multi.yaml", [
        'multi/ABS(AMAX_WIND-BMAX_WIND)_boxplot.png',
        'multi/ABS(AMAX_WIND-BMAX_WIND)_mean.png',
        'multi/ABS(AMAX_WIND-BMAX_WIND)_median.png',
        'multi/ABS(AMAX_WIND-BMAX_WIND)_rank.png',
        'multi/ABS(AMAX_WIND-BMAX_WIND)_relperf.png',
        'multi/ABS(AMAX_WIND-BMAX_WIND)_skill_md.png',
        'multi/ABS(AMAX_WIND-BMAX_WIND)_skill_mn.png',
        'multi/TK_ERR_boxplot.png',
        'multi/TK_ERR_mean.png',
        'multi/TK_ERR_median.png',
        'multi/TK_ERR_rank.png', # note the rank file will differ each run due to the random seed
        'multi/TK_ERR_relperf.png',
        'multi/TK_ERR_skill_md.png',
        'multi/TK_ERR_skill_mn.png',
    ]),
    ("tcmpr_point_tcdiag.yaml", [
        "point_tcdiag/AMAX_WIND-BMAX_WIND_pointplot.png",
        "point_tcdiag/SHEAR_MAGNITUDE_pointplot.png",
    ]),
])
def test_tcmpr_plots(module_setup_env, remove_files, input_yaml, expected_files):
    """Checking that the tcmpr plots are getting created"""

    remove_files(os.environ['TEST_OUTPUT'], expected_files)

    tcmpr.main(f"{os.environ['TEST_DIR']}/{input_yaml}")

    for expected_file in expected_files:
        assert os.path.isfile(f"{os.environ['TEST_OUTPUT']}/{expected_file}")
