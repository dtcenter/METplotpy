import pytest
import os
import shutil
import json
<<<<<<< HEAD
import xarray as xr
from pandas import DatetimeIndex
=======

>>>>>>> 9d4b43f (461: scatter tests and json compare)

# This fixture temporarily sets the working directory
# to the dir containing the test file. This means 
# realative file locations can be used for each test
# file.
# NOTE: autouse=True means this applies to ALL tests.
<<<<<<< HEAD
# Code that updates the cwd inside a test  file is now
# redundant and can be deleted.
=======
# Code that updates the cwd inside test is now redundant
# and can be deleted.
>>>>>>> 9d4b43f (461: scatter tests and json compare)
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
<<<<<<< HEAD

=======
    
>>>>>>> 9d4b43f (461: scatter tests and json compare)

@pytest.fixture
def assert_json_equal():
    def compare_json(fig, expected_json_file):
        """Takes a plotly figure and a json file
        """
        # Treat everything as str for comparison purposes.
        actual = json.loads(fig.to_json(), parse_float=str, parse_int=str)
        with open(expected_json_file) as f:
            expected = json.load(f,parse_float=str, parse_int=str)
<<<<<<< HEAD

=======
        
>>>>>>> 9d4b43f (461: scatter tests and json compare)
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


TEST_NC_DATA = xr.Dataset(
    {
        "precip": xr.DataArray(
            [
                [[0.1, 0.2, 0.3], [0, 1.3, 4], [0, 20, 0]],
                [[0, 0, 0], [0, 0, 0], [0, 0, 0]],
            ],
            coords={
                "lat": [-1, 0, 1],
                "lon": [112, 113, 114],
                "time": DatetimeIndex(["2024-09-25 00:00:00", "2024-09-25 03:00:33"]),
            },
            dims=["time", "lat", "lon"],
            attrs={"long_name": "variable long name"},
        ),
    },
    attrs={"Conventions": "CF-99.9", "history": "History string"},
)

@pytest.fixture()
def nc_test_file(tmp_path_factory):
    """Create a netCDF file with a very small amount of data.
    File is written to a temp directory and the path to the 
    file returned as the fixture value.
    """
    file_name = tmp_path_factory.mktemp("data") / "test_data.nc"
    TEST_NC_DATA.to_netcdf(file_name)
    return file_name

