import pytest
import os
import shutil
import json


# This fixture temporarily sets the working directory
# to the dir containing the test file. This means 
# realative file locations can be used for each test
# file.
# NOTE: autouse=True means this applies to ALL tests.
# Code that updates the cwd inside a test  file is now
# redundant and can be deleted.
@pytest.fixture(autouse=True)
def change_test_dir(request, monkeypatch):
    monkeypatch.chdir(request.fspath.dirname)


def ordered(obj):
    """Recursive function to sort JSON, even lists of dicts with the same keys"""
    if isinstance(obj, dict):
        return sorted((k, ordered(v)) for k, v in obj.items())
    if isinstance(obj, list):
        return sorted(ordered(x) for x in obj)
    else:
        return obj


@pytest.fixture
def assert_json_equal():
    def compare_json(fig, expected_json_file):
        """Takes a plotly figure and a json file
        """
        # Treat everything as str for comparison purposes.
        actual = json.loads(fig.to_json(), parse_float=str, parse_int=str)
        with open(expected_json_file) as f:
            expected = json.load(f,parse_float=str, parse_int=str)

        # Fail with a nice message
        if ordered(actual) == ordered(expected):
            return True
        else:
            message = "This test will fail when there have been changes to plot code but the corresponding" \
                "json test file hasn't been updates. To update the test file run `fig.write_json`"\
                " e.g. `scatter.figure.write_json('custom_scatter_expected.json')`"
            raise AssertionError(message)
    
    return compare_json


@pytest.fixture
def setup_env():
    def set_environ(test_dir):
        print("Setting up environment")
        os.environ['METPLOTPY_BASE'] = f"{test_dir}/../../"
        os.environ['TEST_DIR'] = test_dir
    return set_environ


@pytest.fixture()
def remove_files():
    def remove_the_files(test_dir, file_list):
        print("Removing the files")
        # loop over list of files under test_dir and remove them
        for file in file_list:
            try:
                os.remove(os.path.join(test_dir, file))
            except OSError:
                pass

        # also remove intermed_files directory if it exists
        print("Removing intermed_files directory if it exists")
        try:
            shutil.rmtree(f"{test_dir}/intermed_files")
        except FileNotFoundError:
            pass

    return remove_the_files
