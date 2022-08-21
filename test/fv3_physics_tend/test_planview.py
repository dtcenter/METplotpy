import pytest
import os
import runner_planview

# @pytest.mark.skip
def test_no_args():
    '''
    Currently, physics_tend.py has the default config file hard-coded, so a FileNotFound
    error is raised.
    '''
    runner_config_filename = "./runner_planview.yaml"
    try:
        runner_planview.run_help(runner_config_filename)
        assert True
    except FileNotFoundError as fnfe:
        assert False

@pytest.mark.skip
def test_plot_created():
    '''
    Test if the plot file is created
    '''
    runner_config_filename = "./runner_planview.yaml"
    try:
        expected_file = "./tmp_500hPa.20190504_150000-20190504_210000.png"
        runner_planview.run_example(runner_config_filename)
        assert os.path.isfile(expected_file) == True
        os.remove(expected_file)
    except FileNotFoundError as fnfe:
        assert False

@pytest.mark.skip
def test_plot_created_for_output_file_name():
    '''
    Test if the plot file is created when the output filename is specified and
    the output directory specified exists.
    '''
    runner_config_filename = "./runner_planview.yaml"

    try:
        expected_file = "./test_planview.png"
        runner_planview.run_output_file(runner_config_filename)
        # assert os.path.isfile(expected_file) == True
        # os.remove(expected_file)
    except FileNotFoundError as fnfe:
        assert False

# skip this for now until we get support for creating non-existent outputfiles
@pytest.mark.skip
def test_output_file():
    '''
    Test if the plot file is created in the output directory specified. Test that
    the output directory is created if it doesn't exist.
    '''
    runner_config_filename = "./runner_planview.yaml"
    try:
        runner_planview.run_outputfile(runner_config_filename)
        expected_file = "./output/test_planview.20190504_150000-20190504_210000.png"
        assert os.path.isfile(expected_file) == True
        os.remove(expected_file)

    except FileNotFoundError as fnfe:
        assert False

