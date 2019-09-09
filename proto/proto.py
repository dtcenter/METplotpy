import yaml
import os
import sys


def read_yaml(yaml_full_file):
    '''
        Reads in a yaml file

        Input:
            yaml_full_file:  The full path to the yaml filename to parse

        Returns:
            docs:  The contents of the yaml file
    '''
    # open the config file
    with open(yaml_full_file) as stream:
        try:
            docs = yaml.load(stream, Loader=yaml.FullLoader)
            print(docs)
            return docs
        except yaml.YAMLError as ye:
            print(ye)


if __name__ == "__main__":
    yaml_file = "/Users/minnawin/feature_13_yaml_check/METplotpy/proto/proto.yaml"
    feature_relative_configs = read_yaml(yaml_file)

    for k,v in feature_relative_configs.items():
        print(k)