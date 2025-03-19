import pytest
import os
import sys
import yaml

cwd = os.path.dirname(__file__)

@pytest.fixture
def setup_planview(autouse=True) -> dict:
    """
       Fixture for setting up the planview tests by
       reading in the planview.yaml file and creating a
       dictionary representation of the settings.
    """
    # open and read the test config file
    with open(os.path.join(cwd, "planview.yaml"), 'r') as stream:
        try:
            return yaml.load(stream, Loader=yaml.FullLoader)
        except yaml.YAMLError as exc:
            print(exc)
            sys.exit(1)

