import os
import pytest
import metplotpy.plots.hovmoeller.hovmoeller as hov
from metplotpy.plots import util


cwd = os.path.dirname(__file__)

def dict_to_yaml(data_dict, output_yaml):
    """Write dict as yaml config file."""
    content = "\n".join(["{k}: {v}".format(k=k,v=v) for k,v in data_dict.items()])
    with open(output_yaml, 'w') as f:
        f.write(content)
    return output_yaml


@pytest.mark.skip()
def test_default_plot_images_match(module_setup_env, remove_files):
    '''
        Compare an expected plot with the
        newly created plot to verify that the plot hasn't
        changed in appearance.

        !!!!!WARNING!!!!!:  When run within PyCharm IDE, the hovmoeller_default_plot.png plot
        can sometimes be a different size than the expected (which was generated
        using the same configuration file and data!)
    '''
    default_plot = "hovmoeller_default_plot.png"
    remove_files(os.environ['TEST_OUTPUT'], [default_plot])

    config_file = os.path.join(cwd, "minimal_hovmoeller.yaml")
    hov.main(config_file)

    # default_plot = os.path.join(os.environ['TEST_OUTPUT'], default_plot)
    # expected_file = 'hovmoeller_expected_default.png'
    # actual_file = os.path.join(cwd, expected_file)
    # comparison = CompareImages(default_plot, actual_file)
    # assert comparison.mssim == 1


@pytest.mark.skip("needs large netCDF file to run")
def test_custom_plot_created(module_setup_env, remove_files):
    expected_file = "hovmoeller_custom_plot.png"

    remove_files(os.environ['TEST_OUTPUT'], [expected_file])

    config_file = os.path.join(cwd, "custom_hovmoeller.yaml")
    hov.main(config_file)

    assert os.path.isfile(os.path.join(os.environ['TEST_OUTPUT'], expected_file))

    # This plot should be different from the default-it has different dimensions
    # so the comparison should raise a ValueError
    # default_plot = os.path.join(cwd, 'hovmoeller_expected_default.png')
    # with pytest.raises(ValueError):
    #     CompareImages(default_plot, expected_file)


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


def test_hovmoeller(module_setup_env, remove_files, nc_test_file, assert_json_equal, tmp_path_factory):
    output_dir = os.environ['TEST_OUTPUT']
    out_file = os.path.join(output_dir, "hovmoeller_test.png")

    remove_files(output_dir, [os.path.basename(out_file)])

    config = make_config(nc_test_file, out_file)

    # basic test to see if output writes
    output_yaml = tmp_path_factory.mktemp("data") / "test_hovmoeller.yaml"
    min_yaml = dict_to_yaml(config, output_yaml=str(output_yaml))

    hov.main(min_yaml)

    assert os.path.isfile(out_file)

    # test actual functions from plot object
    plot_obj = hov.Hovmoeller(util.get_params(min_yaml))

    # note: initializing Hovmoeller removes out_file that was previously written

    plot_obj.save_to_file()
    assert os.path.isfile(out_file)

    # check html write out
    plot_obj.write_html()
    base_name, _ = os.path.splitext(config['plot_filename'])
    out_html = f"{base_name}.html"
    assert os.path.isfile(out_html)

    # finally check json plot values
    # to regenerate json file run:
    json_output = os.path.join(output_dir, "hovmoeller_test.json")
    plot_obj.figure.write_json(json_output)
    assert_json_equal(plot_obj.figure, json_output)


def test_get_lat_str(module_setup_env, nc_test_file, tmp_path_factory):
    output_yaml = tmp_path_factory.mktemp("data") / "test_hovmoeller.yaml"
    min_yaml = dict_to_yaml(make_config(nc_test_file, "test.png"), output_yaml)
    plot_obj = hov.Hovmoeller(util.get_params(min_yaml))

    actual = plot_obj.get_lat_str(-4,-2)
    assert actual == "4S - 2S"

    actual = plot_obj.get_lat_str(-4,12)
    assert actual == "4S - 12N"

    actual = plot_obj.get_lat_str(23,90)
    assert actual == "23N - 90N"
