'''
   Utilities that assist in the plotting of series output go here
'''


import yaml

def read_yaml_config()->dict:
    '''
      Reads in the configuration file that contains the input_nc_file_dir, the
      name of the input netCDF file, the variable name of interest, storm number
      of interest, level of interest, and other settings.

    :return: config_dict a dictionary representation of the series_init.yaml file
    '''

    conf_file = "series_init.yaml"
    with open(conf_file,'r') as yml_conf:
        config = yaml.load(yml_conf)

    return config

if __name__ == "__main__":
    # config = read_yaml_config()
    pass
