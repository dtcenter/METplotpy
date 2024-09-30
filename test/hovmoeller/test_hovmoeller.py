import os
import pytest
import metplotpy.plots.hovmoeller.hovmoeller as hov
from metplotpy.plots import util
from metcalcpy.compare_images import CompareImages

def dict_to_yaml(data_dict,
                output_yaml = "test_hovmoeller.yaml"):
    """Write dict as yaml config file."""
    content = "\n".join(["{k}: {v}".format(k=k,v=v) for k,v in data_dict.items()])
    with open(output_yaml, 'w') as f:
        f.write(content)
    return output_yaml


def cleanup(file_to_remove):
    try:
        path = os.getcwd()
        os.remove(os.path.join(path, file_to_remove))
    except OSError as e:
        # Typically when files have already been removed or
        # don't exist.  Ignore.
        pass

@pytest.mark.skip("Requires specific netCDF input")
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

@pytest.mark.skip("needs large netCDF file to run")
def test_custom_plot_created():
    config_file = os.path.join(os.path.dirname(__file__), "custom_hovmoeller.yaml")
    hov.main(config_file)
    custom_plot = "./hovmoeller_custom_plot.png"
    assert os.path.isfile(custom_plot) == True

    # This plot should be different from the default-it has different dimensions
    # so the comparison should raise a ValueError
    default_plot = './hovmoeller_expected_default.png'
    with pytest.raises(ValueError):
        CompareImages(default_plot, custom_plot)

    # Clean up
    cleanup(custom_plot)


def make_config(nc_file, out_file):

    # values here are sensitive to those set
    # in the `nc_test_file` fixture.
    config = {
        "input_data_file": nc_file,
        "plot_filename": out_file,
        "date_start": "2024-09-25",
        "date_end": "2024-09-26",
        "contour_min": 0.1,
        "contour_max": 10,
        "unit_converion": 1,
        "title": "test plot",
        "create_html": "true",
    }
    return config

def test_hovmoeller(nc_test_file,assert_json_equal):
    out_file = "hovmoeller_test.png"
    config = make_config(nc_test_file, out_file)

    # basic test to see if output writes
    min_yaml = dict_to_yaml(config)
    hov.main(min_yaml)

    assert os.path.isfile(out_file)

    # test actual functions from plot object
    plot_obj = hov.Hovmoeller(util.get_params(min_yaml))

    # check html write out
    plot_obj.write_html()
    out_html = config['plot_filename'].split('.')[0] + '.html'
    assert os.path.isfile(out_html)

    # finally check json plot values
    # to regenerate json file run:
    # plot_obj.figure.write_json('hovmoeller_test.json')
    assert_json_equal(plot_obj.figure, 'hovmoeller_test.json')

    # Clean up
    cleanup(out_file)
    cleanup(out_html)

def test_get_lat_str(nc_test_file):
    min_yaml = dict_to_yaml(make_config(nc_test_file, "test.png"))
    plot_obj = hov.Hovmoeller(util.get_params(min_yaml))

    actual = plot_obj.get_lat_str(-4,-2)
    assert actual == "4S - 2S"

    actual = plot_obj.get_lat_str(-4,12)
    assert actual == "4S - 12N"

    actual = plot_obj.get_lat_str(23,90)
    assert actual == "23N - 90N"
