import pytest
import os
import runner_planview

def test_no_args():
    '''
    Run the script with just the help option and the required input files
    '''
    runner_config_filename = "./runner_fv3_phys.yaml"
    try:
        runner_planview.run_help(runner_config_filename)
        assert True
    except FileNotFoundError:
        # to verify that there aren't any hard-coded paths to the config file.
        assert False
    except SystemExit:
        assert False
    except RuntimeError:
        assert False
    except Exception:
        # Catch-all, just in case there are some other exceptions that were raised.
        assert False

def test_plot_created():
    '''
    Test if the plot file is created
    '''
    runner_config_filename = "./runner_fv3_phys.yaml"
    try:
        expected_file = "./tmp_500hPa.png"
        runner_planview.run_planview_500hPa(runner_config_filename)
        assert os.path.isfile(expected_file) == True
        os.remove(expected_file)
    except FileNotFoundError as fnfe:
        assert False

    try:
        expected_file = "./tmp_pbl.png"
        runner_planview.run_planview_pbl(runner_config_filename)
        assert os.path.isfile(expected_file) == True
        os.remove(expected_file)
    except FileNotFoundError as fnfe:
        assert False
