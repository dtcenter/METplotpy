import warnings

import pytest
import os

import pandas as pd

from metplotpy.plots.roc_diagram import roc_diagram as roc
import metcalcpy.util.ctc_statistics as ctc

cwd = os.path.dirname(__file__)


@pytest.mark.parametrize("input_yaml,expected_files", [
    ("CTC_ROC_thresh.yaml", ["CTC_ROC_thresh.png"]),
    ("CTC_ROC_thresh_dump_pts.yaml", ["CTC_ROC_thresh_dump_pts.png", "intermed_files/CTC_ROC_thresh.points1"]),
    ("CTC_ROC_summary.yaml", ["CTC_ROC_summary.png", "intermed_files/CTC_ROC_summary.points1"]),
    ("CTC_ROC_thresh_reverse_pts.yaml", ["CTC_ROC_thresh_reverse_pts.png", "intermed_files_reverse_pts/CTC_ROC_thresh.points1"]),
    ("PCT_ROC.yaml", ["PCT_ROC.png"]),
    ("CTC_wind_reformatted.yaml", ["CTC_wind_reformatted.png"]),
    ("custom_roc_diagram.yaml", ["roc_diagram_custom.png"]),
])
def test_roc_diagram(module_setup_env, remove_files, input_yaml, expected_files):
    """Checking that the plot file is getting created but the points1 file is NOT"""

    remove_files(os.environ['TEST_OUTPUT'], expected_files)

    roc.main(f"{cwd}/{input_yaml}")

    for expected_file in expected_files:
        assert os.path.isfile(f"{os.environ['TEST_OUTPUT']}/{expected_file}")

    if input_yaml == "CTC_ROC_thresh_dump_pts.yaml":
        check_ctc_thresh_dump_points()
    if input_yaml == "CTC_ROC_summary.yaml":
        check_expected_ctc_summary()
    if input_yaml == "CTC_ROC_thresh_reverse_pts.yaml":
        check_expected_ctc_thresh_points_reversed()


def check_ctc_thresh_dump_points():
    """
        For test data, verify that the points in the .points1 file are in the
         directory we specified and the values match what is expected
         (within round-off tolerance/acceptable precision).
    """
    expected_pody = pd.Series([1, 0.8457663, 0.7634846, 0.5093934, 0.1228585, 0])
    expected_pofd = pd.Series([1, 0.0688293, 0.049127, 0.0247044, 0.0048342, 0])
    df = pd.read_csv(f"{os.environ['TEST_OUTPUT']}/intermed_files/CTC_ROC_thresh.points1", sep='\t', header='infer')
    pofd = df.iloc[:, 0]
    pody = df.iloc[:, 1]

    for index, expected in enumerate(expected_pody):
        assert ctc.round_half_up(expected) - ctc.round_half_up(pody[index]) == 0.0

    # if we get here, then all elements matched in value and position

    # do the same test for pofd
    for index, expected in enumerate(expected_pofd):
        assert ctc.round_half_up(expected) - ctc.round_half_up(pofd[index]) == 0.0


def check_expected_ctc_summary():
    """
        For test data, verify that the points in the .points1 file are in the
        directory we specified and the values
        match what is expected (within round-off tolerance/acceptable precision).
    """
    expected_pofd = pd.Series([1, 0.0052708, 0, 1, 0.0084788, 0, 1, 0.0068247, 0])
    expected_pody = pd.Series([1, 0.0878715, 0, 1, 0.1166785, 0, 1, 0.1018776, 0])

    df = pd.read_csv(f"{os.environ['TEST_OUTPUT']}/intermed_files/CTC_ROC_summary.points1", sep='\t', header='infer')
    pofd = df.iloc[:, 0]
    pody = df.iloc[:, 1]

    for index, expected in enumerate(expected_pody):
        assert ctc.round_half_up(expected) - ctc.round_half_up(pody[index]) == 0.0

    # if we get here, then all elements matched in value and position

    # do the same test for pofd
    for index, expected in enumerate(expected_pofd):
        assert ctc.round_half_up(expected) - ctc.round_half_up(pofd[index]) == 0.0


def check_expected_ctc_thresh_points_reversed():
    '''
        For test data, verify that the points in the .points1 file
        match what is expected (within round-off tolerance/acceptable precision) when
        we set reverse_connection_order: 'True'.
    :return:
    '''
    expected_pody = pd.Series([1, 0.8457663, 0.7634846, 0.5093934, 0.1228585, 0])
    expected_pofd = pd.Series([1, 0.0688293, 0.0491275, 0.0247044, 0.0048342, 0])

    df = pd.read_csv(f"{os.environ['TEST_OUTPUT']}/intermed_files_reverse_pts/CTC_ROC_thresh.points1", sep='\t', header='infer')
    pofd = df.iloc[:, 0]
    pody = df.iloc[:, 1]

    for index, expected in enumerate(expected_pody):
        assert ctc.round_half_up(expected) - ctc.round_half_up(pody[index]) == 0.0

    # if we get here, then all elements matched in value and position

    # do the same test for pofd
    for index, expected in enumerate(expected_pofd):
        assert ctc.round_half_up(expected) - ctc.round_half_up(pofd[index]) == 0.0


def test_ee_returns_empty_df(module_setup_env, capsys, remove_files):
    """
        use CTC_ROC.data with event equalization set to True. This will
        result in an empty data frame returned from event equalization. Check for
        expected output message:

        "INFO: No resulting data after performing event equalization of axis 1
         INFO: No points to plot (most likely as a result of event equalization). "
    """
    expected_files = ['CTC_ROC_ee.png']
    remove_files(os.environ['TEST_OUTPUT'], expected_files)

    custom_config_filename = f"{cwd}/CTC_ROC_ee.yaml"

    roc.main(custom_config_filename)

    for expected_file in expected_files:
        assert os.path.isfile(f"{os.environ['TEST_OUTPUT']}/{expected_file}")

    captured = capsys.readouterr()
    expected = '\nINFO: No resulting data after performing event equalization of axis 1\n' \
               'INFO: No points to plot (most likely as a result of event equalization).  \n'
    assert expected in captured.out


def test_pct_no_warnings(module_setup_env, remove_files):
    '''
        Verify that the ROC diagram is generated without FutureWarnings
    '''

    remove_files(os.environ['TEST_OUTPUT'], ['PCT_ROC.png'])

    custom_config_filename = f"{cwd}/PCT_ROC.yaml"
    print("\n Testing for FutureWarning..")
    try:
        roc.main(custom_config_filename)
    except FutureWarning:
        print("FutureWarning generated")
        # FutureWarning generated, test fails
        assert False
