import pytest
import os
import sys
import xarray
import yaml

cwd = os.path.dirname(__file__)
FILE_INFO_CONFIG = "physics_tendency_test.yaml"


@pytest.fixture
def setup_physics_tendency_test(autouse=True) -> dict:
    """
      Reads in the physics_tendency_test.yaml file and creating a
       dictionary representation of those settings which indicate where the
       grid and history files are located (and the data directory location, where additional
       files can be found).
    """
    # open and read the config file that contains file and data location
    with open(os.path.join(cwd, FILE_INFO_CONFIG), 'r') as stream:
        try:
            return yaml.load(stream, Loader=yaml.FullLoader)
        except yaml.YAMLError as exc:
            print(exc)
            sys.exit(1)


def create_config_from_filename(config_name) -> dict:
    """
       Reads in the full filepath config filename (YAML) and creates
       a configuration object (dictionary representation of the settings)
    """
    with open(config_name, 'r') as stream:
        try:
            return yaml.load(stream, Loader=yaml.FullLoader)
        except yaml.YAMLError as exc:
            print(exc)
            sys.exit(1)

def create_physics_tendency_dataset(plot_config_file: str) -> xarray.Dataset:
    """
       Generate the dataset necessary for generating the planview, vertical cross-section, or vertical profile plot

       Input:
         plot_config_file - the filename of the YAML config file used to generate a plot

       Returns:
            an xarray dataset created by the physics tendency module
    """
    plot_test_config = create_config_from_filename(plot_config_file)
    return pt.prepare_ds(plot_test_config, plot_test_config['history_file'],
                         plot_test_config['grid_file'])
