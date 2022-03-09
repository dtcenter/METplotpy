# !!!IMPORTANT!!!
# activate conda environment in the testing subshell
# Replace blenny_363 with your METplus Python 3.6.3
# conda environment name
# !!!!!!!!

# !/usr/bin/env conda run -n blenny_363 python

import pytest
import os
from metplotpy.plots.histogram import prob_hist
from metcalcpy.compare_images import CompareImages


@pytest.fixture
def setup():
    # Cleanup the plotfile  output file from any previous run
    cleanup()


    os.environ['METPLOTPY_BASE'] = "../../../metplotpy"
    custom_config_filename = "prob_hist.yaml"

    prob_hist.main(custom_config_filename)


def cleanup():
    # remove the rel_hist.png
    # from any previous runs
    try:
        path = os.getcwd()
        plot_file = './prob_hist.png'
        os.remove(os.path.join(path, plot_file))
    except OSError as e:
        # Typically when files have already been removed or
        # don't exist.  Ignore.
        pass

@pytest.mark.parametrize("test_input, expected",
                         (["./prob_hist_expected.png", True],
                          ["./prob_hist.png", True]))
def test_files_exist(setup, test_input, expected):
    """
        Checking that the plot and data files are getting created
    """
    assert os.path.isfile(test_input) == expected
    cleanup()

#@pytest.mark.skip("needs updating to reflect changes to histogram code")
def test_images_match(setup):
    """
        Compare an expected plot with the
        newly created plot to verify that the plot hasn't
        changed in appearance.
    """
    comparison = CompareImages("./prob_hist_expected.png",
                               "./prob_hist.png")
    assert comparison.mssim == 1
    cleanup()
