import pytest
import os
import pandas as pd
from metplotpy.plots.roc_diagram import roc_diagram as roc
from metcalcpy.compare_images import CompareImages
import metcalcpy.util.ctc_statistics as ctc


# Fixture used for the image comparison
# test.
@pytest.fixture
def setup():
    # Cleanup the plotfile and point1 output file from any previous run
    cleanup()
    # Set up the METPLOTPY_BASE so that met_plot.py will correctly find
    # the config directory containing all the default config files.
    os.environ['METPLOTPY_BASE'] = "../../"
    custom_config_filename = "./CTC_ROC_thresh.yaml"
    # print("\n current directory: ", os.getcwd())
    # print("\ncustom config file: ", custom_config_filename, '\n')

    # Invoke the command to generate a Performance Diagram based on
    # the test_custom_performance_diagram.yaml custom config file.
    roc.main(custom_config_filename)


@pytest.fixture
def setup_rev_points():
    # Cleanup the plotfile and point1 output file from any previous run
    path = os.getcwd()
    # Set up the METPLOTPY_BASE so that met_plot.py will correctly find
    # the config directory containing all the default config files.
    os.environ['METPLOTPY_BASE'] = "../../"
    custom_config_filename = "./CTC_ROC_thresh_reverse_pts.yaml"
    print("\n current directory: ", os.getcwd())
    print("\ncustom config file: ", custom_config_filename, '\n')

    # Invoke the command to generate a Performance Diagram based on
    # the test_custom_performance_diagram.yaml custom config file.
    roc.main(custom_config_filename)


@pytest.fixture
def setup_dump_points():
    # Cleanup the plotfile and point1 output file from any previous run
    path = os.getcwd()
    # put any intermediate files in the intermed_files subdirectory of this current
    # working directory. *NOTE* This MUST match with what you set up in CTC_ROC_thresh.yaml for the
    # points_path configuration setting.
    subdir_path = os.path.join(path, 'intermed_files')
    # Set up the METPLOTPY_BASE so that met_plot.py will correctly find
    # the config directory containing all the default config files.
    os.environ['METPLOTPY_BASE'] = "../../"
    custom_config_filename = "./CTC_ROC_thresh_dump_pts.yaml"
    # print("\n current directory: ", os.getcwd())
    # print("\ncustom config file: ", custom_config_filename, '\n')
    try:
        os.mkdir(os.path.join(os.getcwd(), 'intermed_files'))
    except FileExistsError as e:
        pass

    # Invoke the command to generate a Performance Diagram based on
    # the test_custom_performance_diagram.yaml custom config file.
    roc.main(custom_config_filename)


def cleanup():
    # remove the performance_diagram_expected.png and plot_20200317_151252.points1 files
    # from any previous runs
    # The subdir_path is where the .points1 file will be stored
    try:
        path = os.getcwd()
        plot_file = 'CTC_ROC_thresh.png'
        html_file = '.html'
        os.remove(os.path.join(path, html_file))
        os.remove(os.path.join(path, plot_file))
    except OSError as e:
        # Typically when files have already been removed or
        # don't exist.  Ignore.
        pass


@pytest.mark.parametrize("test_input,expected_boolean",
                         (["./CTC_ROC_thresh_expected.png", True], ["./CTC_ROC_thresh.points1", False]))
def test_files_exist(setup, test_input, expected_boolean):
    '''
        Checking that the plot file is getting created but the points1 file is NOT
    '''
    assert os.path.isfile(test_input) == expected_boolean
    cleanup()


def test_expected_CTC_thresh_dump_points(setup_dump_points):
    '''
        For test data, verify that the points in the .points1 file are in the
        directory we specified and the values
        match what is expected (within round-off tolerance/acceptable precision).
    :return:
    '''
    expected_pody = pd.Series([1, 0.8457663, 0.7634846, 0.5093934, 0.1228585, 0])
    expected_pofd = pd.Series([1, 0.0688293, 0.049127, 0.0247044, 0.0048342, 0])
    df = pd.read_csv("./intermed_files/CTC_ROC_thresh.points1", sep='\t', header='infer')
    pofd = df.iloc[:, 0]
    pody = df.iloc[:, 1]

    for index, expected in enumerate(expected_pody):
        if ctc.round_half_up(expected) - ctc.round_half_up(pody[index]) == 0.0:
            pass
        else:
            assert False

    # if we get here, then all elements matched in value and position
    assert True

    # do the same test for pofd
    for index, expected in enumerate(expected_pofd):
        if ctc.round_half_up(expected) - ctc.round_half_up(pofd[index]) == 0.0:
            pass
        else:
            assert False

    # different cleanup than what is provided by cleanup()
    # clean up the intermediate subdirectory and other files
    try:
        path = os.getcwd()
        plot_file = 'CTC_ROC_thresh_dump_pts.png'
        html_file = '.html'
        points_file = 'CTC_ROC_thresh.points1'
        intermed_path = os.path.join(path, "intermed_files")
        os.remove(os.path.join(intermed_path, points_file))
        os.rmdir(intermed_path)
        os.remove(os.path.join(path, plot_file))
        os.remove(os.path.join(path, html_file))
    except OSError as e:
        # Typically when files have already been removed or
        # don't exist.  Ignore.
        pass

    # if we get here, then all elements matched in value and position
    assert True


def test_expected_CTC_thresh_points_reversed(setup_rev_points):
    '''
        For test data, verify that the points in the .points1 file
        match what is expected (within round-off tolerance/acceptable precision) when
        we set reverse_connection_order: 'True'.
    :return:
    '''
    expected_pody = pd.Series([1, 0.8457663, 0.7634846, 0.5093934, 0.1228585, 0])
    expected_pofd = pd.Series([1, 0.0688293, 0.0491275, 0.0247044, 0.0048342, 0])

    df = pd.read_csv("./CTC_ROC_thresh.points1", sep='\t', header='infer')
    pofd = df.iloc[:, 0]
    pody = df.iloc[:, 1]

    for index, expected in enumerate(expected_pody):
        if ctc.round_half_up(expected) - ctc.round_half_up(pody[index]) == 0.0:
            pass
        else:
            assert False

        # if we get here, then all elements matched in value and position
    assert True

    # do the same test for pofd
    for index, expected in enumerate(expected_pofd):
        if ctc.round_half_up(expected) - ctc.round_half_up(pofd[index]) == 0.0:
            pass
        else:
            assert False

        # if we get here, then all elements matched in value and position
    assert True

    # different cleanup than what is provided by cleanup()
    try:
        path = os.getcwd()
        plot_file = 'CTC_ROC_thresh.png'
        points_file = 'CTC_ROC_thresh.points1'
        html_file = '.html'
        os.remove(os.path.join(path, points_file))
        os.remove(os.path.join(path, plot_file))
        os.remove(os.path.join(path, html_file))
    except OSError as e:
        # Typically when files have already been removed or
        # don't exist.  Ignore.
        pass


def test_ee_returns_empty_df(capsys):
    '''
        use CTC_ROC.data with event equalization set to True. This will
        result in an empty data frame returned from event equalization. Check for
        expected output message:

        "INFO: No resulting data after performing event equalization of axis 1
         INFO: No points to plot (most likely as a result of event equalization). "


    '''
    custom_config_filename = "./CTC_ROC_ee.yaml"
    roc.main(custom_config_filename)
    captured = capsys.readouterr()
    expected = '\nINFO: No resulting data after performing event equalization of axis 1\n' \
               'INFO: No points to plot (most likely as a result of event equalization).  \n'
    # print('\n\noutput from capsys: ', captured.out)
    # print('\nexpected:', expected)
    assert captured.out == expected

    # Clean up
    try:
        path = os.getcwd()
        plot_file = 'CTC_ROC_ee.png'
        os.remove(os.path.join(path, plot_file))
    except OSError as e:
        # Typically when files have already been removed or
        # don't exist.  Ignore.
        pass

@pytest.mark.skip("skip image comparison")
def test_images_match(setup):
    '''
        Compare an expected plot with the
        newly created plot to verify that the plot hasn't
        changed in appearance.

        !!!!!WARNING!!!!!:  When run within PyCharm IDE, the CTC_ROC_thresh.png plot
        can sometimes be a different size than the expected (which was generated
        using the same configuration file and data!)
    '''
    path = os.getcwd()
    plot_file = './CTC_ROC_thresh.png'
    actual_file = os.path.join(path, plot_file)
    comparison = CompareImages('./CTC_ROC_thresh.png', actual_file)
    assert comparison.mssim == 1

    # cleanup
    # different cleanup than what is provided by cleanup()
    try:
        plot_file = 'CTC_ROC_thresh.png'
        html_file = '.html'
        os.remove(os.path.join(path, plot_file))
        os.remove(os.path.join(path, html_file))
    except OSError as e:
        # Typically when files have already been removed or
        # don't exist.  Ignore.
        pass
