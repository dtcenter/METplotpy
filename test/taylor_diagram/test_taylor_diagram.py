import os
from metplotpy.plots.taylor_diagram import taylor_diagram as td
#from metcalcpy.compare_images import CompareImages

cwd = os.path.dirname(__file__)


def test_pos_corr_file_exists(setup_env):
    setup_env(cwd)

    test_config_filename = f"{cwd}/test_pos_corr.yaml"
    td.main(test_config_filename)

    # Verify that a plot was generated
    plot_file = f"{cwd}/test_pos_corr_plot.png"
    expected_file = f"{cwd}/expected_pos_corr_plot.png"
    assert os.path.isfile(plot_file)

    # image comparison
    #comparison = CompareImages(plot_file,expected_file)
    # assert comparison.mssim >= .99

    # Clean up
    os.remove(plot_file)


def test_pos_corr_file_exists(setup_env):
    setup_env(cwd)
    test_config_filename = f"{cwd}/test_pos_corr.yaml"
    td.main(test_config_filename)

    # Verify that a plot was generated
    plot_file = f"{cwd}/test_pos_corr_plot.png"
    assert os.path.isfile(plot_file)

    # Clean up
    os.remove(plot_file)

# Not reliable when the expected image is generated on a Mac and then this
# test is run on non-Mac machine.
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


def test_neg_and_pos_corr_file_exists(setup_env):
    setup_env(cwd)
    test_config_filename = f"{cwd}/test_neg_and_pos_corr.yaml"
    td.main(test_config_filename)

    # Verify that a plot was generated
    plot_file = f"{cwd}/test_neg_and_pos_corr_plot.png"
    assert os.path.isfile(plot_file)

    # Clean up
    os.remove(plot_file)


# Not reliable when the expected image is generated on a Mac and then this
# test is run on non-Mac machine.
def test_neg_and_pos_corr_images_match(setup_env):
    setup_env(cwd)
    test_config_filename = f"{cwd}/test_neg_and_pos_corr.yaml"
    td.main(test_config_filename)

    # Verify that a plot was generated
    plot_file = f"{cwd}/test_neg_and_pos_corr_plot.png"
    expected_file = f"{cwd}/expected_neg_and_pos_corr_plot.png"

    # image comparison, with allowance of .99 match instead of 100% match
    #comparison = CompareImages(plot_file, expected_file)
    #assert comparison.mssim >= .99

    # Clean up
    os.remove(plot_file)


def test_custom_plot_exists(setup_env):
    setup_env(cwd)
    test_config_filename = f"{cwd}/taylor_diagram_custom.yaml"
    td.main(test_config_filename)

    # Verify that a plot was generated
    plot_file = f"{cwd}/taylor_diagram_custom.png"
    assert os.path.isfile(plot_file)

    # Clean up
    os.remove(plot_file)
