import pytest
import os
from conftest import create_config_from_filename, cleanup
import metplotpy.contributed.fv3_physics_tend.vert_profile_fv3 as vp
import metplotpy.contributed.fv3_physics_tend.physics_tend as pt

cwd = os.path.dirname(__file__)


@pytest.mark.skip("skip because dataset is too large")
@pytest.mark.parametrize("test_config, expected", ([f"{cwd}/tmp_500hPa.yaml", f"{cwd}/tmp.vert_profile.png"],))
def test_plot_created(setup_physics_tendency_test, test_config, expected):
    """
       Test if the plot file is created
    """
    plot_config_obj = create_config_from_filename(test_config)
    ds = pt.prepare_ds(plot_config_obj, setup_physics_tendency_test['history_file'],
                       setup_physics_tendency_test['grid_file'])

    # Generate the vertical profile  plot based on the settings from the test config files
    data_directory = setup_physics_tendency_test['data_dir']
    if plot_config_obj['shp'] is not None:
        shapefile = os.path.join(data_directory, plot_config_obj['shp'])
    else:
        shapefile = plot_config_obj['shp']

    # using settings in the config file
    vert_profile_obj = vp.vert_profile(plot_config_obj, ds, shp=shapefile,twindow=plot_config_obj['twindow'],xmin=plot_config_obj['xmin'],
                                       xmax=plot_config_obj['xmax'])
    ofile = f"{plot_config_obj['statevarname']}.vert_profile.png"
    if plot_config_obj["shp"]:
        shp = plot_config_obj["shp"].rstrip("/")
        # Add shapefile name to output filename
        shapename = os.path.basename(shp)
        root, ext = os.path.splitext(ofile)
        ofile = root + f".{shapename}" + ext
    output_file = os.path.join(f"{cwd}", ofile)
    vert_profile_obj.savefig(output_file, dpi=plot_config_obj["dpi"])

    # plots will be generated in the same directory where the tests reside
    assert os.path.exists(expected)
    cleanup(expected)


@pytest.mark.skip("skip because dataset is too large")
@pytest.mark.parametrize("test_config, expected", ([f"{cwd}/tmp_500hPa.yaml", "tmp_vert_profile.MID_CONUS.png"],))
def test_plot_different_settings(setup_physics_tendency_test, test_config, expected):
    """
       Test if the plot file is a minimum size (not empty plot)
    """
    plot_config_obj = create_config_from_filename(test_config)
    ds = pt.prepare_ds(plot_config_obj, setup_physics_tendency_test['history_file'],
                       setup_physics_tendency_test['grid_file'])

    # Generate the vertical profile  plot based on the settings from the test config files
    plot_src_directory = setup_physics_tendency_test['plot_src_dir']

    # explicitly use the MID_CONUS shapefiles
    shapefile = os.path.join(plot_src_directory, "shapefiles/MID_CONUS")

    # Use values that aren't in the config file
    xmin_val = -0.002
    xmax_val = 0.002
    twindow_val = 1

    # set ofile to a different location, the root directory
    root_dir = os.path.dirname(os.path.abspath(__file__))
    ofile_val = f"{root_dir}/tmp_vert_profile.MID_CONUS.png"
    vert_profile_obj = vp.vert_profile(plot_config_obj, ds, shp=shapefile,twindow=twindow_val,xmin=xmin_val,
                                       xmax=xmax_val, ofile =ofile_val)
    vert_profile_obj.savefig(ofile_val, dpi=plot_config_obj["dpi"])

    # plots will be generated in the same directory where the tests reside
    expected_file = os.path.join(root_dir, expected)
    assert os.path.exists(expected_file)

    # Assume anything less than 5kb is an 'empty' plot
    assert os.path.getsize(expected_file) > 50000
    cleanup(expected_file)


@pytest.mark.skip("skip because dataset is too large")
@pytest.mark.parametrize("test_config, expected", ([f"{cwd}/tmp_500hPa.yaml", f"{cwd}/tmp.vert_profile.png"],))
def test_plot_not_empty(setup_physics_tendency_test, test_config, expected):
    """
       Test if the plot file is a minimum size (not empty plot)
    """
    plot_config_obj = create_config_from_filename(test_config)
    ds = pt.prepare_ds(plot_config_obj, setup_physics_tendency_test['history_file'],
                       setup_physics_tendency_test['grid_file'])

    # Generate the vertical profile plot based on the settings from the test config files
    plot_src_directory = setup_physics_tendency_test['plot_src_dir']
    if plot_config_obj['shp'] is not None:
        shapefile = os.path.join(plot_src_directory, plot_config_obj['shp'])
    else:
        shapefile = plot_config_obj['shp']

    vert_profile_obj = vp.vert_profile(plot_config_obj, ds, shp=shapefile,twindow=plot_config_obj['twindow'],xmin=plot_config_obj['xmin'],
                                       xmax=plot_config_obj['xmax'])

    ofile = f"{plot_config_obj['statevarname']}.vert_profile.png"
    if plot_config_obj["shp"]:
        shp = plot_config_obj["shp"].rstrip("/")
        # Add shapefile name to output filename
        shapename = os.path.basename(shp)
        root, ext = os.path.splitext(ofile)
        ofile = root + f".{shapename}" + ext
    output_file = os.path.join(f"{cwd}", ofile)
    vert_profile_obj.savefig(output_file, dpi=plot_config_obj["dpi"])

    # plots will be generated in the same directory where the tests reside
    assert os.path.exists(expected)

    # Assume that plots less than 5kb are empty
    assert os.path.getsize(expected) > 50000
    cleanup(expected)

