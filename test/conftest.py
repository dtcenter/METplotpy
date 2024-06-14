import pytest
import os
import shutil


@pytest.fixture
def setup_env():
    def set_environ(test_dir):
        os.environ['METPLOTPY_BASE'] = f"{test_dir}/../../"
        os.environ['TEST_DIR'] = test_dir
    return set_environ


@pytest.fixture()
def remove_files():
    def remove_the_files(test_dir, file_list):
        # loop over list of files under test_dir and remove them
        for file in file_list:
            try:
                os.remove(os.path.join(test_dir, file))
            except OSError:
                pass

        # also remove intermed_files directory if it exists
        try:
            shutil.rmtree(f"{test_dir}/intermed_files")
        except FileNotFoundError:
            pass

    return remove_the_files
