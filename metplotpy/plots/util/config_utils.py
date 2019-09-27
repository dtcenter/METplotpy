"""
Module:  for METplotpy plots that use INI config files. Utilities for transforming
         produtil config objects (which represent the content in INI formatted configuration files)
         into a dictionary representation.
 """
__author__ = "Minna Win"
__email__ = 'met_help@ucar.edu'

def get_config_dict(config):
    """

        Input:
           @param config: The METplusConfig configuration object created by the METplus and produtil modules
                          (which use Python's ConfigParser)
        Return:
           config_dict:  A dictionary (actually a dictionary of dictionaries) that represent the
                         INI-formatted configuration file.
    """

    # Read in the config object that was created by the METplus' config_metplus.setup() and create
    # a dictionary of dictionaries that represent the INI formatted config file.
    # For a config file that looks like the following:
    # [dir]
    #  input_dir = 'foo'
    #  output_dir = 'bar'
    # [config]
    #  setting1 = 'a'
    #  setting2 = 'b'
    # The dictionary representation of this should look like the following:
    # {'dir': {'input_dir':'foo', 'output_dir':'bar'}, 'config': {'setting1':'a', 'setting2':'b'}}

    # the sections correspond to the outermost keys in the dictionary
    all_sections = config.sections()
    config_dict = {}
    for section in all_sections:
        value = config.items(section)
        outer_key = section

        inner_dict = {}
        for val in value:
            inner_key = val[0]
            inner_value = val[1]
            inner_dict[inner_key] = inner_value

        config_dict[outer_key] = inner_dict

    return config_dict
