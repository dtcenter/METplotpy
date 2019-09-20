import yaml
import os

"""Exploratory code to determine how to achieve parsing of a YAML file that embodies all the
   required behavior of an INI configuration file.  Currently, in the METplus wrappers, we are
   using INI config files and performing configuration file "management" via METplus wrapper modules and the
   HWRF produtil modules in conjunction with Python's ConfigParser.
"""

def read_yaml(yaml_full_file):
    '''
        Reads in a yaml file that exercises the features that are currently observed in the METplus wrapper
        config files (INI type config files which are parsed via Python's ConfigParser and special cases are
        handled via HWRF's produtil package).

        Input:
            yaml_full_file:  The full path to the yaml filename to parse

        Returns:
            docs:  The contents of the yaml file
    '''
    # open the config file, assume that there is only one document per YAML file,
    # to minimize confusion and errors in user-created YAML config files.
    with open(yaml_full_file) as stream:
        try:
            docs = yaml.safe_load(stream)
            print(docs)
            return docs
        except yaml.YAMLError as ye:
            print(ye)

def get_all_sections(yaml_doc):
    '''
    Returns a list of section headers.
    Input:
        @param yaml_doc: The parsed YAML config file.
    Returns:
        for now, prints out the headers found in the YAML file.
    '''


    # The sections in the config file
    print("\n===========\n Sections \n===========")
    for k, v in feature_relative_configs.items():
        print(k)

    sections_list = [k for k in feature_relative_configs.keys() ]
    print("=============\n\n")

    return sections_list

def get_all_executables(all_config_entries, sections):
    """
    Parses the executable dictionary and returns a list of the non-MET
    executables defined in the YAML config file.
    Input:
        @param all_config_entries: the entire dictionary hierarchy from the YAML config file
        @param sections:
    Returns:
        execs_list:  A list of the executables
    """
    print("====================\nnon-MET Executables \n====================\n")

    # First, check if we have an 'exe' section, if not, error out.
    if 'exe' in sections:
        # check if there are any entries in the section, if not, then return an
        # empty execs_list
        if all_config_entries['exe']:
            exe_dicts = all_config_entries['exe']
            exe_list = [v for v in exe_dicts.values()]
            print("exe values: ", exe_list)

            # Get the value of the current environment variable via os.environ[key]
            for env_var in exe_list:
                print("for {}, value = {}".format( env_var, os.environ[env_var]))
            return exe_list
        else:
            print("No executables defined")
            return []

        return exe_list
    else:
        raise ValueError('No executable section found in YAML config file.')



if __name__ == "__main__":
    yaml_file = "/Users/minnawin/feature_13_yaml_check/METplotpy/proto/proto.yaml"
    feature_relative_configs = read_yaml(yaml_file)
    sections = get_all_sections(feature_relative_configs)
    try:
        e_list = get_all_executables(feature_relative_configs, sections)
    except ValueError as ve:
        print(ve)



