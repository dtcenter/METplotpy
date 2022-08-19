import pytest
import os
import runner_planview

def setup():
    # Cleanup the plotfile and point1 output file from any previous run
    cleanup()
    runner_config_filename = "./runner_planview.yaml"
    return runner_config_filename

def cleanup():
    ''' Remove any files and directories created during testing'''
    pass

def test_no_args():
    '''
    Currently, physics_tend.py has the default config file hard-coded, so a FileNotFound
    error is raised.
    '''
    runner_config_filename = setup()
    try:
        runner_planview.run_help(runner_config_filename)
        assert True
    except FileNotFoundError as fnfe:
        assert False