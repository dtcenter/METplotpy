import warnings

import pytest
import os
import pandas as pd
from metplotpy.plots.roc_diagram import roc_diagram as roc
from metcalcpy.compare_images import CompareImages
import metcalcpy.util.ctc_statistics as ctc

cwd = os.path.dirname(__file__)


# Fixture used for the image comparison
# test.
@pytest.fixture
def setup(setup_env):
    # Cleanup the plotfile and point1 output file from any previous run
    cleanup()
    setup_env(cwd)
    custom_config_filename = f"{cwd}/CTC_ROC_thresh.yaml"
    # print("\n current directory: ", os.getcwd())
    # print("\ncustom config file: ", custom_config_filename, '\n')

    # Invoke the command to generate a Performance Diagram based on
    # the test_custom_performance_diagram.yaml custom config file.
    roc.main(custom_config_filename)


@pytest.fixture
def setup_rev_points(setup_env):
    # Cleanup the plotfile and point1 output file from any previous run
    cleanup()
    setup_env(cwd)
    custom_config_filename = f"{cwd}/CTC_ROC_thresh_reverse_pts.yaml"
    print("\n current directory: ", cwd)
    print("\ncustom config file: ", custom_config_filename, '\n')

    # Invoke the command to generate a Performance Diagram based on
    # the test_custom_performance_diagram.yaml custom config file.
    roc.main(custom_config_filename)


@pytest.fixture
def setup_summary(setup_env):
    # Cleanup the plotfile and point1 output file from any previous run
    cleanup()
    setup_env(cwd)
    custom_config_filename = f"{cwd}/CTC_ROC_summary.yaml"

    try:
        os.mkdir(os.path.join(cwd, 'intermed_files'))
    except FileExistsError:
        pass

    # Invoke the command to generate a Performance Diagram based on
    # the test_custom_performance_diagram.yaml custom config file.
    roc.main(custom_config_filename)


@pytest.fixture
def setup_dump_points(setup_env):
    # Cleanup the plotfile and point1 output file from any previous run
    cleanup()
    setup_env(cwd)
    # put any intermediate files in the intermed_files subdirectory of this current
    # working directory. *NOTE* This MUST match with what you set up in CTC_ROC_thresh.yaml for the
    # points_path configuration setting.
    custom_config_filename = f"{cwd}/CTC_ROC_thresh_dump_pts.yaml"
    # print("\n current directory: ", os.getcwd())
    # print("\ncustom config file: ", custom_config_filename, '\n')
    try:
        os.mkdir(os.path.join(cwd, 'intermed_files'))
    except FileExistsError:
        pass

    # Invoke the command to generate a Performance Diagram based on
    # the test_custom_performance_diagram.yaml custom config file.
    roc.main(custom_config_filename)


def cleanup():
    # remove the performance_diagram_expected.png and plot_20200317_151252.points1 files
    # from any previous runs
    # The subdir_path is where the .points1 file will be stored
    try:
        plot_file = 'CTC_ROC_thresh.png'
        html_file = 'CTC_ROC_thresh.html'
        os.remove(os.path.join(cwd, html_file))
        os.remove(os.path.join(cwd, plot_file))
    except OSError:
        pass


@pytest.mark.parametrize("test_input,expected_boolean",
                         (["CTC_ROC_thresh_expected.png", True], ["CTC_ROC_thresh.points1", False]))
def test_files_exist(setup, test_input, expected_boolean):
    '''
        Checking that the plot file is getting created but the points1 file is NOT
    '''
    assert os.path.isfile(f"{cwd}/{test_input}") == expected_boolean
    cleanup()


def test_expected_ctc_thresh_dump_points(setup_dump_points, remove_files):
    '''
        For test data, verify that the points in the .points1 file are in the
        directory we specified and the values
        match what is expected (within round-off tolerance/acceptable precision).
    :return:
    '''
    expected_pody = pd.Series([1, 0.8457663, 0.7634846, 0.5093934, 0.1228585, 0])
    expected_pofd = pd.Series([1, 0.0688293, 0.049127, 0.0247044, 0.0048342, 0])
    df = pd.read_csv(f"{cwd}/intermed_files/CTC_ROC_thresh.points1", sep='\t', header='infer')
    pofd = df.iloc[:, 0]
    pody = df.iloc[:, 1]

    for index, expected in enumerate(expected_pody):
        assert ctc.round_half_up(expected) - ctc.round_half_up(pody[index]) == 0.0

    # if we get here, then all elements matched in value and position

    # do the same test for pofd
    for index, expected in enumerate(expected_pofd):
        assert ctc.round_half_up(expected) - ctc.round_half_up(pofd[index]) == 0.0

    # different cleanup than what is provided by cleanup()
    # clean up the intermediate subdirectory and other files
    remove_files(cwd, ['CTC_ROC_thresh_dump_pts.png', 'CTC_ROC_thresh_dump_pts.html'])


def test_expected_ctc_summary(setup_summary, remove_files):
    '''
        For test data, verify that the points in the .points1 file are in the
        directory we specified and the values
        match what is expected (within round-off tolerance/acceptable precision).
    :return:
    '''
    expected_pofd = pd.Series([1, 0.0052708, 0, 1, 0.0084788, 0, 1, 0.0068247, 0])
    expected_pody = pd.Series([1, 0.0878715, 0, 1, 0.1166785, 0, 1, 0.1018776, 0])

    df = pd.read_csv(f"{cwd}/intermed_files/CTC_ROC_summary.points1", sep='\t', header='infer')
    pofd = df.iloc[:, 0]
    pody = df.iloc[:, 1]

    for index, expected in enumerate(expected_pody):
        assert ctc.round_half_up(expected) - ctc.round_half_up(pody[index]) == 0.0

    # if we get here, then all elements matched in value and position

    # do the same test for pofd
    for index, expected in enumerate(expected_pofd):
        assert ctc.round_half_up(expected) - ctc.round_half_up(pofd[index]) == 0.0

    # different cleanup than what is provided by cleanup()
    # clean up the intermediate subdirectory and other files
    remove_files(cwd, ['CTC_ROC_summary.png', 'CTC_ROC_summary.html'])


def test_expected_ctc_thresh_points_reversed(setup_rev_points, remove_files):
    '''
        For test data, verify that the points in the .points1 file
        match what is expected (within round-off tolerance/acceptable precision) when
        we set reverse_connection_order: 'True'.
    :return:
    '''
    expected_pody = pd.Series([1, 0.8457663, 0.7634846, 0.5093934, 0.1228585, 0])
    expected_pofd = pd.Series([1, 0.0688293, 0.0491275, 0.0247044, 0.0048342, 0])

    df = pd.read_csv(f"{cwd}/CTC_ROC_thresh.points1", sep='\t', header='infer')
    pofd = df.iloc[:, 0]
    pody = df.iloc[:, 1]

    for index, expected in enumerate(expected_pody):
        assert ctc.round_half_up(expected) - ctc.round_half_up(pody[index]) == 0.0

    # if we get here, then all elements matched in value and position

    # do the same test for pofd
    for index, expected in enumerate(expected_pofd):
        assert ctc.round_half_up(expected) - ctc.round_half_up(pofd[index]) == 0.0

    # if we get here, then all elements matched in value and position

    # different cleanup than what is provided by cleanup()
    remove_files(cwd, ['CTC_ROC_thresh.png', 'CTC_ROC_thresh.points1', 'CTC_ROC_thresh.html'])


def test_ee_returns_empty_df(capsys, remove_files):
    '''
        use CTC_ROC.data with event equalization set to True. This will
        result in an empty data frame returned from event equalization. Check for
        expected output message:

        "INFO: No resulting data after performing event equalization of axis 1
         INFO: No points to plot (most likely as a result of event equalization). "


    '''
    custom_config_filename = f"{cwd}/CTC_ROC_ee.yaml"
    roc.main(custom_config_filename)
    captured = capsys.readouterr()
    expected = '\nINFO: No resulting data after performing event equalization of axis 1\n' \
               'INFO: No points to plot (most likely as a result of event equalization).  \n'
    # print('\n\noutput from capsys: ', captured.out)
    # print('\nexpected:', expected)
    assert captured.out == expected

    # Clean up
    remove_files(cwd, ['CTC_ROC_ee.png', 'CTC_ROC_ee.html'])


def test_images_match(setup, remove_files):
    '''
        Compare an expected plot with the
        newly created plot to verify that the plot hasn't
        changed in appearance.

        !!!!!WARNING!!!!!:  When run within PyCharm IDE, the CTC_ROC_thresh.png plot
        can sometimes be a different size than the expected (which was generated
        using the same configuration file and data!)
    '''
    plot_file = 'CTC_ROC_thresh.png'
    actual_file = os.path.join(cwd, plot_file)
    comparison = CompareImages(f'{cwd}/CTC_ROC_thresh.png', actual_file)
    assert comparison.mssim == 1

    # cleanup
    # different cleanup than what is provided by cleanup()
    remove_files(cwd, ['CTC_ROC_thresh.png', 'CTC_ROC_thresh.html'])


def test_pct_plot_exists(remove_files):
    '''
        Verify that the ROC diagram is generated
    '''

    custom_config_filename = f"{cwd}/PCT_ROC.yaml"
    output_plot = f"{cwd}/PCT_ROC.png"

    print("\n Testing for existence of PCT ROC plot...")
    roc.main(custom_config_filename)
    assert os.path.isfile(output_plot)
    remove_files(cwd, ['PCT_ROC.png', 'PCT_ROC.html'])


def test_pct_no_warnings(remove_files):
    '''
        Verify that the ROC diagram is generated without FutureWarnings
    '''

    custom_config_filename = f"{cwd}/PCT_ROC.yaml"
    print("\n Testing for FutureWarning..")

    try:
        roc.main(custom_config_filename)
    except FutureWarning:
        print("FutureWarning generated")
        # FutureWarning generated, test fails
        assert False

    remove_files(cwd, ['PCT_ROC.png', 'PCT_ROC.html'])


def test_ctc_reformatted(remove_files):
    '''
        Verify that the ROC diagram is generated successfully
        from reformatted CTC data.
    '''

    custom_config_filename = f"{cwd}/CTC_wind_reformatted.yaml"
    output_plot = f"{cwd}/CTC_wind_reformatted.png"

    print("\n Testing for presence of the CTC_wind_reformatted.png plot...")

    roc.main(custom_config_filename)
    assert os.path.isfile(output_plot)
    # Checking for plot size isn't reliable
    #expected_filesize = int(43239)
    #plot_filesize =  int(os.path.getsize(output_plot))
    #assert plot_filesize >= expected_filesize
    remove_files(cwd, ['CTC_wind_reformatted.png', 'CTC_wind_reformatted.html'])
