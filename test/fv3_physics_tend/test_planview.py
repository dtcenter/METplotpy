import pytest
import os
import runner_planview

@pytest.mark.skip()
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

@pytest.mark.skip()
def test_plot_created():
    '''
    Test if the plot file is created
    '''
    runner_config_filename = "./runner_fv3_phys.yaml"
    try:
        expected_file = "./tmp_500hPa.png"
        runner_planview.run_example(runner_config_filename)
        assert os.path.isfile(expected_file) == True
        os.remove(expected_file)
    except FileNotFoundError as fnfe:
        assert False

@pytest.mark.skip()
def test_plot_created_for_output_file_name():
    '''
    Test if the plot file is created when the output filename is specified when
    the specified output directory exists.
    '''
    runner_config_filename = "./runner_fv3_phys.yaml"

    try:
        expected_file = "./test_planview.png"
        runner_planview.run_with_novel_output_file(runner_config_filename)
        assert os.path.isfile(expected_file) == True
        os.remove(expected_file)
    except FileNotFoundError as fnfe:
        assert False

@pytest.mark.skip()
def test_novel_output_dir():
    '''
    Test if the plot file is created in the non-existent output directory. Test that
    the output directory is created if it doesn't exist.
    '''
    runner_config_filename = "./runner_fv3_phys.yaml"
    try:
        runner_planview.run_with_novel_output_dir(runner_config_filename)
        expected_file = "./output/test_planview.png"
        assert os.path.isfile(expected_file) == True
        os.remove(expected_file)
        os.removedirs("./output")


    except FileNotFoundError as fnfe:
        assert False

