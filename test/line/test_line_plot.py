import pandas as pd
import pytest
import os
from metplotpy.plots.line import line as l


# from metcalcpy.compare_images import CompareImages


@pytest.fixture
def setup():
    # Cleanup the plotfile and point1 output file from any previous run
    cleanup()
    # Set up the METPLOTPY_BASE so that met_plot.py will correctly find
    # the config directory containing all the default config files.
    os.environ['METPLOTPY_BASE'] = "../../"
    custom_config_filename = "custom_line.yaml"

    # Invoke the command to generate a line plot based on
    # the custom config file.
    l.main(custom_config_filename)


def cleanup():
    # remove the line.png and .points files
    # from any previous runs
    try:
        path = os.getcwd()
        plot_file = 'line.png'
        points_file_1 = 'line.points1'
        points_file_2 = 'line.points2'
        os.remove(os.path.join(path, plot_file))
        os.remove(os.path.join(path, points_file_1))
        os.remove(os.path.join(path, points_file_2))
    except OSError as e:
        # Typically when files have already been removed or
        # don't exist.  Ignore.
        pass


@pytest.mark.parametrize("test_input,expected",
                         (["./line.png", True], ["./line.points1", False],
                          ["./line.points2", False]))
def test_files_exist(setup, test_input, expected):
    '''
        Checking that the plot file is getting created but the
        .points1 and .points2 files are NOT
    '''
    assert os.path.isfile(test_input) == expected
    cleanup()


@pytest.mark.parametrize("test_input,expected",
                         (["./line.png", True], ["./intermed_files/line.points1", True],
                          ["./intermed_files/line.points2", True]))
def test_points_files_exist(test_input, expected):
    '''
        Checking that the plot and point data files are getting created
    '''

    # create the intermediate directory to store the .points1 and .points2 files
    try:
        os.mkdir(os.path.join(os.getcwd(), 'intermed_files'))
    except FileExistsError as e:
        pass

    os.environ['METPLOTPY_BASE'] = "../../"
    custom_config_filename = "custom_line2.yaml"
    l.main(custom_config_filename)

    # Test for expected values
    assert os.path.isfile(test_input) == expected

    # cleanup intermediate files and plot
    try:
        path = os.getcwd()
        plot_file = 'line.png'
        points_file_1 = 'line.points1'
        points_file_2 = 'line.points2'
        intermed_path = os.path.join(path, 'intermed_files')
        os.remove(os.path.join(path, plot_file))
        os.remove(os.path.join(intermed_path, points_file_1))
        os.remove(os.path.join(intermed_path, points_file_2))
    except OSError as e:
        # Typically when files have already been removed or
        # don't exist.  Ignore.
        pass


def test_no_nans_in_points_files():
    '''
        Checking that the point data files do not have any NaN's
    '''

    # create the intermediate directory to store the .points1 and .points2 files
    try:
        os.mkdir(os.path.join(os.getcwd(), 'intermed_files'))
    except FileExistsError as e:
        pass

    os.environ['METPLOTPY_BASE'] = "../../"
    custom_config_filename = "custom_line2.yaml"
    l.main(custom_config_filename)

    # Check for NaN's in the intermediate files, line.points1 and line.points2
    # Fail if there are any NaN's-this indicates something went wrong with the
    # line_series.py module's  _create_series_points() method.
    nans_found = False
    with open("./intermed_files/line.points1", "r") as f:
        data = f.read()
        if "NaN" in data:
            nans_found = True

    assert nans_found == False

    # Now check line.points2
    with open("./intermed_files/line.points2", "r") as f:
        data = f.read()
        if "NaN" in data:
            nans_found = True

    assert nans_found == False

    # Verify that the nan.points1 file does indeed trigger a "nans_found"
    with open("./intermed_files/nan.points1", "r") as f:
        data = f.read()
        if "NaN" in data:
            nans_found = True

    # assert
    assert nans_found == True

    # cleanup intermediate files and plot
    try:
        path = os.getcwd()
        plot_file = 'line.png'
        points_file_1 = 'line.points1'
        points_file_2 = 'line.points2'
        intermed_path = os.path.join(path, 'intermed_files')
        os.remove(os.path.join(path, plot_file))
        os.remove(os.path.join(intermed_path, points_file_1))
        os.remove(os.path.join(intermed_path, points_file_2))
        os.remove("./intermed_files/nan.points1")
    except OSError as e:
        # Typically when files have already been removed or
        # don't exist.  Ignore.
        pass


@pytest.mark.skip()
def test_images_match(setup):
    '''
        Compare an expected plot with the
                 newly created plot to verify that the plot hasn't
         changed in appearance.
     '''
    path = os.getcwd()
    plot_file = './line.png'
    actual_file = os.path.join(path, plot_file)
    comparison = CompareImages('./line_expected.png', actual_file)

    # !!!WARNING!!! SOMETIMES FILE SIZES DIFFER IN SPITE OF THE PLOTS LOOKING THE SAME
    # THIS TEST IS NOT 100% RELIABLE because of differences in machines, OS, etc.
    assert comparison.mssim == 1
    cleanup()


@pytest.mark.skip()
def test_new_images_match():
    '''
        Compare an expected plot with the start_at_zero option, with the
        newly created plot to verify that the plot hasn't
        changed in appearance.
     '''

    # Set up the METPLOTPY_BASE so that met_plot.py will correctly find
    # the config directory containing all the default config files.
    os.environ['METPLOTPY_BASE'] = "../../"
    custom_config_filename = "custom_line_from_zero.yaml"

    # Invoke the command to generate a Performance Diagram based on
    # the test_custom_performance_diagram.yaml custom config file.
    l.main(custom_config_filename)
    path = os.getcwd()
    plot_file = 'line_from_zero.png'
    actual_file = os.path.join(path, plot_file)
    comparison = CompareImages('./line_expected_from_zero.png', actual_file)

    # !!!WARNING!!! SOMETIMES FILE SIZES DIFFER IN SPITE OF THE PLOTS LOOKING THE SAME
    # THIS TEST IS NOT 100% RELIABLE because of differences in machines, OS, etc.
    assert comparison.mssim == 1

    # cleanup plot
    try:
        path = os.getcwd()
        plot_file = 'line_from_zero.png'
        os.remove(os.path.join(path, plot_file))
    except OSError as e:
        # Typically when files have already been removed or
        # don't exist.  Ignore.
        pass


def test_vertical_plot():
    '''

     Test that the y1 values from the Python version of the vertical plot
     match the y1 values from the METviewer Rplot version of the vertical plot.
     Avoid relying on image comparison tests.

    '''

    # create the intermediate directory to store the .points1 and .points2 files
    try:
        os.mkdir(os.path.join(os.getcwd(), 'intermed_files'))
    except FileExistsError as e:
        pass

    os.environ['METPLOTPY_BASE'] = "../../"
    custom_config_filename = "mv_custom_vert_line.yaml"
    l.main(custom_config_filename)

    try:
        path = os.getcwd()
        plot_file = 'vert_line_plot.png'
        points_file_1 = 'vert_line_plot.points1'
        points_file_2 = 'vert_line_plot.points2'
        intermed_path = os.path.join(path, 'intermed_files')

        # Retrieve the .points1 files generated by METviewer and METplotpy respectively
        mv_df = pd.read_csv('./intermed_files/vert_plot_y1_from_metviewer.points1',
                            sep=" ", header=None)
        mpp_df = pd.read_csv('./intermed_files/vert_line_plot.points1', sep=" ",
                             header=None)

        # -----------------------
        # Compare various values
        # -----------------------
        # Verify we are comparing data frames created from the same data
        # Same number of rows:
        assert mv_df.shape[0] == mpp_df.shape[0]
        # Same number of columns:
        assert mv_df.shape[1] == mpp_df.shape[1]

        # Values for each column are the same (accounting for precision between R and
        # Python and
        # different host machines)
        for col in range(mv_df.shape[1]):
            mv_col: pd.Series = mv_df.loc[:, col]
            mpp_col: pd.Series = mpp_df.loc[:, col]
            col_diff: pd.Series = mv_col - mpp_col
            sum_diff: float = abs(col_diff.sum())

            # Allow for differences in arithmetic between machines and differences in
            # R vs Python arithmetic
            # allow difference out to 5th significant figure.
            assert sum_diff < 0.00001

        # cleanup intermediate files and plot
        os.remove(os.path.join(path, plot_file))
        os.remove(os.path.join(intermed_path, points_file_1))
        os.remove(os.path.join(intermed_path, points_file_2))
        os.remove('./intermed_files/vert_plot_y1_from_metviewer.points1')
    except OSError as e:
        # Typically when files have already been removed or
        # don't exist.  Ignore.
        pass


def test_fixed_var_val():
    """
        Verify that the fixed_vars_vals_input setting reproduces the
        same data points that METviewer produces.

    """
    # Set up the METPLOTPY_BASE so that met_plot.py will correctly find
    # the config directory containing all the default config files.
    os.environ['METPLOTPY_BASE'] = "../../"
    custom_config_filename = "fbias_fixed_vars_vals.yaml"

    # Invoke the command to generate a line plot based on
    # the custom config file.
    l.main(custom_config_filename)

    expected_points = "../intermed_files/mv_fixed_var_vals.points1"

    try:
        path = os.getcwd()
        plot_file = 'fbias_fixed_vars_reformatted_input.png'

        intermed_path = os.path.join(path, 'intermed_files')

        # Retrieve the .points1 files generated by METviewer and METplotpy respectively
        mv_df = pd.read_csv('./intermed_files/mv_fixed_var_vals.points1',
                            sep="\t", header=None)
        mpp_df = pd.read_csv('./fbias.points1', sep="\t", header=None)

        # Verify that the values in the generated points1 file are identical
        # to those in the METviewer points1 file.

        # First, verify that the points1 files have the same shape
        num_mv_rows = mv_df.shape[0]
        num_mv_cols = mv_df.shape[1]
        num_mpp_rows = mpp_df.shape[0]
        num_mpp_cols = mpp_df.shape[1]

        assert num_mv_rows == num_mpp_rows
        assert num_mv_cols == num_mpp_cols

        # Verify that all of the rows of both have identical values
        for i in range(num_mv_rows):
            assert mv_df.iloc[i][0] == mpp_df.iloc[i][0]

        # Clean up the fbias.points1,  fbias.points2, and .png files
        os.remove('fbias.points1')
        os.remove('fbias.points2')
        os.remove('fbias_fixed_vars_reformatted_input.png')
        os.remove('./intermed_files/mv_fixed_var_vals.points1')
        os.remove(expected_points)
        os.rmdir('./intermed_files')

    except OSError as e:
        # Typically when files have already been removed or
        # don't exist.  Ignore.
        pass


@pytest.mark.skip("Image comparison for development only due to differences in hosts")
def test_fixed_var_val_image_compare():
    """
        Verify that the fixed_vars_vals_input setting reproduces the
        expected plot.

    """
    from metcalcpy.compare_images import CompareImages

    # Set up the METPLOTPY_BASE so that met_plot.py will correctly find
    # the config directory containing all the default config files.
    os.environ['METPLOTPY_BASE'] = "../../"
    custom_config_filename = "fbias_fixed_vars_vals.yaml"

    # Invoke the command to generate a line plot based on
    # the custom config file.
    l.main(custom_config_filename)

    expected_plot = "./expected_fbias_fixed_vars.png"

    try:
        path = os.getcwd()
        plot_file = 'fbias_fixed_vars.png'

        created_file = os.path.join(path, plot_file)

        # first verify that the output plot was created
        if os.path.exists(created_file):
            assert True
        else:
            assert False

        comparison = CompareImages(expected_plot, created_file)

        # !!!WARNING!!! SOMETIMES FILE SIZES DIFFER IN SPITE OF THE PLOTS LOOKING THE
        # SAME
        # THIS TEST IS NOT 100% RELIABLE because of differences in machines, OS, etc.
        assert comparison.mssim == 1

        # Clean up the fbias.points1, fbias.points2 and the png files
        os.remove('fbias.points1')
        os.remove('fbias.points2')
        os.remove(created_file)

    except OSError as e:
        # Typically when files have already been removed or
        # don't exist.  Ignore.
        pass
