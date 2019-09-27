import pytest
import config_metplus
import config_utils as cu

@pytest.fixture(scope='module')
def config():
    """ Create a METplusConfig (ProdutilConfig) configuration object which is a
        representation of a combination of default and custom INI formatted
        configuration files.

    """

    baseinputconfs = ['metplus_config/metplus_system.conf',
                      'metplus_config/metplus_data.conf',
                      'metplus_config/metplus_runtime.conf',
                      'metplus_config/metplus_logging.conf']
    config = config_metplus.setup(baseinputconfs)
    print("config: ", config)
    return config

def test_dict_repr(config):
    """ Verify that a dictionary representation of the
        configuration file has been correctly created by the
        get_dict_of_config() function in the config_utils module.

    """
    expected_keys = ['config', 'dir', 'exe', 'filename_templates']
    # in the util_test.conf file, set the OUTPUT_BASE to /tmp and the
    # log dir to {OUTPUT_BASE} check that the values to these keys
    # is correct.
    expected_output_dir = '/tmp'
    expected_log_dir = expected_output_dir
    config_dict = cu.get_config_dict(config)
    print(type(config_dict))
    assert isinstance(config_dict, dict)
    keys = config_dict.keys()
    for key in keys:
        assert key in expected_keys

    # verify that the expected key,value pair is found
    exp_key, exp_val = 'OUTPUT_BASE', '/tmp'
    assert exp_key in config_dict['dir'].keys() and exp_val in config_dict['dir'][exp_key]

    # verify that the {OUTPUT_BASE} assignment for the LOG_DIR was correctly interpolated (where interpolation is
    # the ability to use variables from other sections of a config file and is supported in Python's ConfigParser
    # library)
    actual_log_val = config_dict['dir']['LOG_DIR']
    assert expected_log_dir == actual_log_val
