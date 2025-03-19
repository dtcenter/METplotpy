import pytest
import os

import xarray
import yaml
import sys
import metplotpy.contributed.fv3_physics_tend.physics_tend as pt
import metplotpy.contributed.fv3_physics_tend.planview_fv3 as pv

cwd = os.path.dirname(__file__)


def cleanup(generated_plot):
    """
      Clean up generated plots
    """
    if os.path.isfile(generated_plot):
        os.remove(generated_plot)




@pytest.mark.skip("skip because dataset is too large")
@pytest.mark.parametrize("test_config, expected", ([f"{cwd}/tmp_500hPa.yaml", "tmp_500hPa.png"],
                                                  [f"{cwd}/tmp_pbl.yaml", "tmp_pbl.png"]))
def test_planview_plot_created(setup_planview, test_config, expected):
    """
    Test if each planview plot file is created
    """

    test_config_obj = create_config_from_filename(test_config)
    ds:xarray.Dataset = create_phys_tendency_dataset(setup_planview, test_config_obj)

    # Generate the planview plot based on the settings from the test config files
    planview_obj = pv.planview(test_config_obj, ds, pfull=test_config_obj['pfull'], robust=test_config_obj['robust'],
                                     shp=test_config_obj['shp'], twindow=test_config_obj['twindow'],
                                     validtime=test_config_obj['validtime'])
    ofile = pv.default_ofile(test_config_obj)
    planview_obj.fig.savefig(ofile, dpi=test_config_obj["dpi"])

    expected_plot = os.path.join(f"{cwd}", expected)
    assert os.path.exists(expected_plot)


@pytest.mark.skip("skip because dataset is too large")
@pytest.mark.parametrize("test_config, expected", ([f"{cwd}/tmp_500hPa.yaml", "tmp_500hPa.png"],
                                                  [f"{cwd}/tmp_pbl.yaml", "tmp_pbl.png"]))
def test_planview_plot_not_empty(setup_planview, test_config, expected):
    """
    Test if each planview plot file is NOT empty
    """

    test_config_obj = create_config_from_filename(test_config)
    ds:xarray.Dataset = create_phys_tendency_dataset(setup_planview, test_config_obj)

    # Generate the planview plot based on the settings from the test config files
    planview_obj = pv.planview(test_config_obj, ds, pfull=test_config_obj['pfull'], robust=test_config_obj['robust'],
                                     shp=test_config_obj['shp'], twindow=test_config_obj['twindow'],
                                     validtime=test_config_obj['validtime'])
    ofile = pv.default_ofile(test_config_obj)
    planview_obj.fig.savefig(ofile, dpi=test_config_obj["dpi"])

    expected_plot = os.path.join(f"{cwd}", expected)

    # Check for empty plot
    # Use a 3 kb size as lowest expected size of the plots to be generated
    assert os.stat(expected_plot).st_size > 300000
    cleanup(expected_plot)

def create_phys_tendency_dataset(setup_planview:dict, test_config:dict) -> xarray.Dataset:
    """
       Generate the dataset necessary for generating the planview plot
    """

    return pt.prepare_ds(test_config, setup_planview['history_file'], setup_planview['grid_file'])



def create_config_from_filename(config_name) -> dict:
    """
       Reads in the full filepath config filename (YAML) and creates
       a configuration object (dictionary representation of the settings)
    """
    with open(config_name, 'r') as stream:
        try:
            return yaml.load(stream, Loader=yaml.FullLoader)
        except yaml.YAMLError as exc:
            print(exc)
            sys.exit(1)

