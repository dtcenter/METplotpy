import os
import pytest
import metplotpy.plots.hovmoeller.hovmoeller as hov
from metcalcpy.compare_images import CompareImages

def cleanup(file_to_remove):
    try:
        path = os.getcwd()
        os.remove(os.path.join(path, file_to_remove))
    except OSError as e:
        # Typically when files have already been removed or
        # don't exist.  Ignore.
        pass


# @pytest.mark.skip("needs large netCDF file to run")
def test_default_plot_created():
    config_file = os.path.join(os.path.dirname(__file__), "minimal_hovmoeller.yaml")
    hov.main(config_file)
    default_plot = "./hovmoeller_default_plot.png"
    assert os.path.isfile(default_plot) == True

    # Clean up
    cleanup(default_plot)

@pytest.mark.skip()
def test_default_plot_images_match():
    '''
        Compare an expected plot with the
        newly created plot to verify that the plot hasn't
        changed in appearance.

        !!!!!WARNING!!!!!:  When run within PyCharm IDE, the hovmoeller_default_plot.png plot
        can sometimes be a different size than the expected (which was generated
        using the same configuration file and data!)
    '''
    config_file = os.path.join(os.path.dirname(__file__), "minimal_hovmoeller.yaml")
    hov.main(config_file)
    default_plot = "./hovmoeller_default_plot.png"
    path = os.getcwd()
    plot_file = './hovmoeller_expected_default.png'
    actual_file = os.path.join(path, plot_file)
    comparison = CompareImages(default_plot, actual_file)
    assert comparison.mssim == 1

    # Clean up
    cleanup(default_plot)

# @pytest.mark.skip("needs large netCDF file to run")
def test_custom_plot_created():
    config_file = os.path.join(os.path.dirname(__file__), "custom_hovmoeller.yaml")
    hov.main(config_file)
    custom_plot = "./hovmoeller_custom_plot.png"
    assert os.path.isfile(custom_plot) == True

    # This plot should be different from the default-it has different dimensions
    # so the comparison should raise a ValueError
    default_plot = './hovmoeller_expected_default.png'
    with pytest.raises(ValueError):
        comparison = CompareImages(default_plot, custom_plot)

    # Clean up
    cleanup(default_plot)