import pytest
import os
import xarray
from conftest import create_config_from_filename, cleanup
import metplotpy.contributed.fv3_physics_tend.planview_fv3 as pv
import metplotpy.contributed.fv3_physics_tend.physics_tend as pt

cwd = os.path.dirname(__file__)



@pytest.mark.skip("skip because dataset is too large")
@pytest.mark.parametrize("test_config, expected", ([f"{cwd}/tmp_500hPa.yaml", f"{cwd}/tmp_500hPa.png"],
                                                  [f"{cwd}/tmp_pbl.yaml", f"{cwd}/tmp_pbl.png"]))
def test_planview_plot_created(setup_physics_tendency_test, test_config, expected):
    """
    Test if each planview plot file is created
    """
    plot_config_obj = create_config_from_filename(test_config)
    ds = pt.prepare_ds(plot_config_obj, setup_physics_tendency_test['history_file'],
                         setup_physics_tendency_test['grid_file'])

    # Generate the planview plot based on the settings from the test config files
    planview_obj = pv.planview(plot_config_obj, ds, pfull=plot_config_obj['pfull'], robust=plot_config_obj['robust'],
                                     shp=plot_config_obj['shp'], twindow=plot_config_obj['twindow'],
                                     validtime=plot_config_obj['validtime'])
    ofile = pv.default_ofile(plot_config_obj)
    planview_obj.fig.savefig(ofile, dpi=plot_config_obj["dpi"])

    # plots will be generated in the same directory where the tests reside
    assert os.path.exists(expected)
    cleanup(expected)


@pytest.mark.skip("skip because dataset is too large")
@pytest.mark.parametrize("test_config, expected", ([f"{cwd}/tmp_500hPa.yaml", "tmp_500hPa.png"],
                                                  [f"{cwd}/tmp_pbl.yaml", "tmp_pbl.png"]))
def test_planview_plot_not_empty(setup_physics_tendency_test, test_config, expected):
    """
    Test if each planview plot file is NOT empty
    """

    test_config_obj = create_config_from_filename(test_config)
    ds:xarray.Dataset = pt.prepare_ds(test_config_obj, setup_physics_tendency_test['history_file'],
                       setup_physics_tendency_test['grid_file'])
    # Generate the planview plot based on the settings from the test config files
    planview_obj = pv.planview(test_config_obj, ds, pfull=test_config_obj['pfull'], robust=test_config_obj['robust'],
                                     shp=test_config_obj['shp'], twindow=test_config_obj['twindow'],
                                     validtime=test_config_obj['validtime'])
    ofile = pv.default_ofile(test_config_obj)
    planview_obj.fig.savefig(ofile, dpi=test_config_obj["dpi"])

    expected_plot = os.path.join(f"{cwd}", expected)
    assert os.path.exists(expected_plot)


    # Check for empty plot
    # Use a 3 kb size as lowest expected size of the plots to be generated
    assert os.stat(expected_plot).st_size > 300000
    cleanup(expected_plot)




