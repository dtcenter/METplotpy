import pytest
import os
import xarray
import metplotpy.contributed.fv3_physics_tend.physics_tend as pt
import metplotpy.contributed.fv3_physics_tend.cross_section_vert as cs
from conftest import create_config_from_filename, cleanup

cwd = os.path.dirname(__file__)

@pytest.mark.skip()
@pytest.mark.parametrize("test_config, expected", ([f"{cwd}/ugrd_500hPa.yaml", f"{cwd}/ugrd_28N-120E-26N-75E.png"],)
                         )

def test_vert_cross_plot_created(setup_physics_tendency_test, test_config, expected):
    """
      Test if the vertical cross-section plot file is created
    """
    plot_config_obj = create_config_from_filename(test_config)
    ds: xarray.Dataset = pt.prepare_ds(plot_config_obj, setup_physics_tendency_test['history_file'],
                                       setup_physics_tendency_test['grid_file'])

    # Generate the cross-section plot based on the settings from the test config files
    plot_src_dir = setup_physics_tendency_test['plot_src_dir']
    if plot_config_obj['shp'] is not None:
        shapefile = os.path.join(plot_src_dir, plot_config_obj['shp'])
    else:
        shapefile = plot_config_obj['shp']

    cross_section_obj = cs.cross_section_vert(plot_config_obj, ds, statevarname=plot_config_obj['statevarname'],
                                         twindow=plot_config_obj['twindow'], shp=shapefile)
    startpt = plot_config_obj["startpt"]
    endpt = plot_config_obj["endpt"]
    ofile = f"{plot_config_obj['statevarname']}_{startpt[0]}N{startpt[1]}E-{endpt[0]}N{endpt[1]}E.png"
    full_outfile = os.path.join(f"{cwd}", ofile)
    cross_section_obj.fig.savefig(full_outfile, dpi=plot_config_obj["dpi"])

    # plots will be generated in the same directory where the tests reside
    assert os.path.exists(expected)

    cleanup(expected)

@pytest.mark.skip()
@pytest.mark.parametrize("test_config, expected", ([f"{cwd}/ugrd_500hPa.yaml", f"{cwd}/ugrd_28N-120E-26N-75E.png"],)
                         )

def test_vert_cross_plot_not_empty(setup_physics_tendency_test, test_config, expected):
    """
      Test if the vertical cross-section plot file is not empty
    """
    plot_config_obj = create_config_from_filename(test_config)
    ds: xarray.Dataset = pt.prepare_ds(plot_config_obj, setup_physics_tendency_test['history_file'],
                                       setup_physics_tendency_test['grid_file'])

    # Generate the cross-section plot based on the settings from the test config files
    plot_src_dir = setup_physics_tendency_test['plot_src_dir']
    if plot_config_obj['shp'] is not None:
        shapefile = os.path.join(plot_src_dir, plot_config_obj['shp'])
    else:
        shapefile = plot_config_obj['shp']

    cross_section_obj = cs.cross_section_vert(plot_config_obj, ds, statevarname=plot_config_obj['statevarname'],
                                         twindow=plot_config_obj['twindow'], shp=shapefile)
    startpt = plot_config_obj["startpt"]
    endpt = plot_config_obj["endpt"]
    ofile = f"{plot_config_obj['statevarname']}_{startpt[0]}N{startpt[1]}E-{endpt[0]}N{endpt[1]}E.png"
    full_outfile = os.path.join(f"{cwd}", ofile)
    cross_section_obj.fig.savefig(full_outfile, dpi=plot_config_obj["dpi"])

    # plots will be generated in the same directory where the tests reside
    # Use 2kb as minimum size to determine if the plot is empty
    assert os.stat(expected).st_size > 200000
    cleanup(expected)


