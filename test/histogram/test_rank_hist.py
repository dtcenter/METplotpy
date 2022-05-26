import os
from metplotpy.plots.histogram import rank_hist
from metcalcpy.compare_images import CompareImages


@pytest.fixture
def setup():
    # Cleanup the plotfile  output file from any previous run
    cleanup()
    # Set up the METPLOTPY_BASE so that met_plot.py will correctly find
    # the config directory containing all the default config files.
    os.environ['METPLOTPY_BASE'] = "../../"
    custom_config_filename = "rank_hist.yaml"

    rank_hist.main(custom_config_filename)


def cleanup():
    # remove the rel_hist.png
    # from any previous runs
    try:
        path = os.getcwd()
        plot_file = './rank_hist.png'
        os.remove(os.path.join(path, plot_file))
    except OSError as e:
        # Typically when files have already been removed or
        # don't exist.  Ignore.
        pass

@pytest.mark.parametrize("test_input, expected",
                         (["./rank_hist_expected.png", True],
                          ["./rank_hist.png", True]))
def test_files_exist(setup, test_input, expected):
    """
        Checking that the plot and data files are getting created
    """
    assert os.path.isfile(test_input) == expected
    cleanup()

@pytest.mark.skip("Image comparisons fail during Github Actions checks.")
def test_images_match(setup):
    """
        Compare an expected plot with the
        newly created plot to verify that the plot hasn't
        changed in appearance.
    """
    comparison = CompareImages("./rank_hist_expected.png",
                               "./rank_hist.png")
    assert comparison.mssim == 1
    cleanup()
