import os
import sys
sys.path.append("../../")
import pytest
from plots.taylor_diagram import taylor_diagram as td
from metcalcpy.compare_images import CompareImages


def test_pos_corr_file_exists():
    os.environ['METPLOTPY_BASE'] = "../../metplotpy"
    test_config_filename = "test_pos_corr.yaml"
    td.main(test_config_filename)

    # Verify that a plot was generated
    plot_file = "test_pos_corr_plot.png"
    expected_file = "expected_pos_corr_plot.png"
    path = os.getcwd()
    assert os.path.isfile(plot_file) == True


    # image comparison
    comparison = CompareImages(plot_file,expected_file)
    assert comparison.mssim >= .99

    # Clean up
    os.remove(os.path.join(path, plot_file))


def test_pos_corr_file_exists():
    os.environ['METPLOTPY_BASE'] = "../../metplotpy"
    test_config_filename = "test_pos_corr.yaml"
    td.main(test_config_filename)

    # Verify that a plot was generated
    plot_file = "test_pos_corr_plot.png"
    path = os.getcwd()
    assert os.path.isfile(plot_file) == True

    # Clean up
    os.remove(os.path.join(path, plot_file))

# def test_pos_corr_images_match():
#          os.environ['METPLOTPY_BASE'] = "../../metplotpy"
#          test_config_filename = "test_pos_corr.yaml"
#          td.main(test_config_filename)
#
#          # Verify that a plot was generated
#          plot_file = "test_pos_corr_plot.png"
#          expected_file = "expected_pos_corr_plot.png"
#          path = os.getcwd()
#
#          # image comparison
#          comparison = CompareImages(plot_file, expected_file)
#          assert comparison.mssim >= .99
#
#          # Clean up
#          os.remove(os.path.join(path, plot_file))

def test_neg_and_pos_corr_file_exists():
    os.environ['METPLOTPY_BASE'] = "../../metplotpy"
    test_config_filename = "test_neg_and_pos_corr.yaml"
    td.main(test_config_filename)

    # Verify that a plot was generated
    plot_file = "test_neg_and_pos_corr_plot.png"
    path = os.getcwd()
    assert os.path.isfile(plot_file) == True

    # Clean up
    os.remove(os.path.join(path, plot_file))

# Not reliable when the expected image is generated on a Mac and then this
# test is run on another machine.
# def test_neg_and_pos_corr_images_match():
#     os.environ['METPLOTPY_BASE'] = "../../metplotpy"
#     test_config_filename = "test_neg_and_pos_corr.yaml"
#     td.main(test_config_filename)
#
#     # Verify that a plot was generated
#     plot_file = "test_neg_and_pos_corr_plot.png"
#     expected_file = "expected_neg_and_pos_corr_plot.png"
#     path = os.getcwd()
#
#     # image comparison, with allowance of .99 match instead of 100% match
#     comparison = CompareImages(plot_file, expected_file)
#     assert comparison.mssim >= .99
#
#     # Clean up
#     os.remove(os.path.join(path, plot_file))

def test_custom_plot_exists():
    os.environ['METPLOTPY_BASE'] = "../../metplotpy"
    test_config_filename = "taylor_diagram_custom.yaml"
    td.main(test_config_filename)

    # Verify that a plot was generated
    plot_file = "./taylor_diagram_custom.png"
    path = os.getcwd()
    assert os.path.isfile(plot_file) == True

    # Clean up
    os.remove(os.path.join(path, plot_file))
