import pytest
import os
import re
import metplotpy.plots.tcmpr_plots.tcmpr as t


@pytest.fixture
def setup():

    # Set up the METPLOTPY_BASE so that met_plot.py will correctly find
    # the config directory containing all the default config files.
    os.environ['METPLOTPY_BASE'] = "../.."
    custom_config_filename = "./test_tcmpr_multi_plots.yaml"

    # Invoke the command to generate a line plot based on
    # the custom config file
    t.main(custom_config_filename)



def test_plots_created(setup):



    # Check for presence of fourteen plots (seven plot types, one each for the
    # ABS(X-Y) and TK_ERR columns.
    expected_num_plots = 14
    test_dir = os.getcwd()
    output_dir = os.path.join(test_dir, 'output')
    only_files = os.listdir(output_dir)
    assert len(only_files) == expected_num_plots

    size_abs_boxplot = 221448
    size_abs_mean = 173448
    size_abs_median = 184775
    size_abs_rank = 255637
    size_abs_relperf = 117889
    size_abs_skill_md = 198979
    size_abs_skill_mn = 185594
    size_tk_boxplot = 192259
    size_tk_mean = 146980
    size_tk_median = 152591
    size_tk_rank = 189702
    size_tk_relperf = 157972
    size_tk_skill_md = 171571
    size_tk_skill_mn = 159396
    expected_sizes = {'ABS(AMAX_WIND-BMAX_WIND)_boxplot.png':size_abs_boxplot,
                      'ABS(AMAX_WIND-BMAX_WIND)_mean.png':size_abs_mean,
                      'ABS(AMAX_WIND-BMAX_WIND)_median.png':size_abs_median,
                      'ABS(AMAX_WIND-BMAX_WIND)_relperf.png':size_abs_relperf,
                      'ABS(AMAX_WIND-BMAX_WIND)_skill_md.png':size_abs_skill_md,
                      'ABS(AMAX_WIND-BMAX_WIND)_skill_mn.png':size_abs_skill_mn,
                      'TK_ERR_boxplot.png':size_tk_boxplot, 'TK_ERR_mean.png':size_tk_mean,
                      'TK_ERR_median.png':size_tk_median,
                      'TK_ERR_relperf.png':size_tk_relperf, 'TK_ERR_skill_md.png':size_tk_skill_md,
                      'TK_ERR_skill_mn.png':size_tk_skill_mn
                      }

    # Check that filenames are what we expect
    expected_names_list = ['ABS(AMAX_WIND-BMAX_WIND)_boxplot.png', 'ABS(AMAX_WIND-BMAX_WIND)_mean.png',
                           'ABS(AMAX_WIND-BMAX_WIND)_median.png',
                           'ABS(AMAX_WIND-BMAX_WIND)_rank.png', 'ABS(AMAX_WIND-BMAX_WIND)_relperf.png',
                           'ABS(AMAX_WIND-BMAX_WIND)_skill_md.png',
                           'ABS(AMAX_WIND-BMAX_WIND)_skill_mn.png',
                           'TK_ERR_boxplot.png', 'TK_ERR_mean.png', 'TK_ERR_median.png', 'TK_ERR_rank.png',
                           'TK_ERR_relperf.png', 'TK_ERR_skill_md.png', 'TK_ERR_skill_mn.png']

    for cur_file in only_files:
        assert cur_file in expected_names_list

    # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    # ONLY RUN THESE TESTS ON A LOCAL MACHINE, they are not reliable when run in Github Actions container
    #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    # Check that file sizes (in bytes) are consistent (cannot check rank files, the confidence
    # intervals are generated using random seed-they will not be identical from one run to another
    # for cur_file in only_files:
    #     match = re.match(r'.+_(mean).png', cur_file)
    #     if match:
    #       cur_file_size = int(os.path.getsize(os.path.join(output_dir, cur_file)))
    #       expected_size = int(expected_sizes[cur_file])
    #       assert cur_file_size >= expected_size
    #


    # Clean up
    try:
        for cur_file in only_files:
            os.remove(os.path.join(output_dir, cur_file))
        os.rmdir(output_dir)
    except FileNotFoundError:
        # If files already cleaned up, then ignore error
        pass