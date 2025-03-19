import pytest
import os
import sys
import yaml

cwd = os.path.dirname(__file__)

@pytest.fixture
def setup_physics_tendency_test(autouse=True) -> dict:
    """
       Fixture for setting up the planview tests by
       reading in the physics_tendency_test.yaml file and creating a
       dictionary representation of the settings.
    """
    # open and read the test config file
    with open(os.path.join(cwd, "physics_tendency_test.yaml"), 'r') as stream:
        try:
            return yaml.load(stream, Loader=yaml.FullLoader)
        except yaml.YAMLError as exc:
            print(exc)
            sys.exit(1)

