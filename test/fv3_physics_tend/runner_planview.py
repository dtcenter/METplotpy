import os
import sys
import yaml

'''
Runner script used to generate variations of the plan view plot.  Each function represents a
different scenario.  The pytest script will invoke the individual functions as part of the testing.
This is a work-around since the plotting scripts are comprised of a combination of positional and other
optional command line arguments.

Requires a configuration file that has the history and grid input files in addition to the location of 
the planview_fv3.py file
'''


def run_help(config_file):
    ''' Run the planview_fv3.py with only the -h (help) '''
    config = open_config(config_file)
    command_str = "python " + config['source_dir'] + "/planview_fv3.py " + " ./fv3_physics_tend_defaults.yaml " + \
                  config['history_file'] + " " + config['grid_file'] + " -h"
    os.system(command_str)


def run_example(config_file):
    '''Run the example in the user's guide'''
    config = open_config(config_file)
    command_str = "python " + config['source_dir'] + "/planview_fv3.py " + " ./fv3_physics_tend_defaults.yaml " + \
                  config['history_file'] + " " + config[
                      'grid_file'] + " tmp pbl -p 500 -t 1 -v 20190504T14 --nofineprint "

    print("command string: ", command_str)
    os.system(command_str)


def run_with_novel_output_file(config_file):
    '''Run the example in the user's guide with a novel output file name'''
    config = open_config(config_file)
    command_str = "python " + config['source_dir'] + "/planview_fv3.py " + " ./fv3_physics_tend_defaults.yaml " + \
                  config['history_file'] + " " + config[
                      'grid_file'] + " tmp pbl -p 500 -t 1 -v 20190504T14 --nofineprint -o ./test_planview.png"
    print("command string: ", command_str)
    os.system(command_str)

def run_with_novel_output_dir(config_file):
        '''Run the example in the user's guide specifying a non-existent output directory'''
        config = open_config(config_file)
        command_str = "python " + config['source_dir'] + "/planview_fv3.py " + " ./fv3_physics_tend_defaults.yaml " + \
                      config['history_file'] + " " + config['grid_file']+ " tmp pbl -p 500 -t 1 -v 20190504T14 --nofineprint \
                       -o ./output/test_planview.png"
        print("command string: ", command_str)
        os.system(command_str)


def open_config(config_file):
    with open(config_file, 'r') as stream:
        try:
            config_obj = yaml.load(stream, Loader=yaml.FullLoader)
        except yaml.YAMLError as exc:
            print(exc)
    return config_obj


if __name__ == "__main__":
    config_file = sys.argv[1]
    # run_help(config_file)
    # run_example(config_file)
    run_with_novel_output_file(config_file)
    # run_with_novel_output_dir(config_file)
