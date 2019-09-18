import os.path
import sys
import collections
import pytest
#sys.path.insert(0, "../../../../METplus/ush/")
import config_metplus
import histo_metplus


@pytest.fixture(scope='module')
def config():
    return config_metplus.setup()

# def test_metplus_final(config):
#     """
#           Verify that the metplus_final.conf file was created in the /tmp
#           directory.
#
#        """
#     assert config
#
# def test_all_sections(config):
#     """
#        Verify that all the sections retrieved from the config
#        file are what we expected.
#
#
#     """
#     all_sections = config.sections()
#     expected_sections = ['config', 'dir', 'exe', 'filename_templates', 'regex_pattern']
#
#     for section in all_sections:
#         if section not in expected_sections:
#             assert False
#     else:
#         assert True


def test_dir_section(config):
    """ Verify that the values for the keys in the
        [dir] section are what are expected.  All are set
        to /tmp, except for the PARM_BASE.
    """
    dir_items = config.items('dir')
    print("dir items: ", dir_items)
    for item in dir_items:

        print('value: ', item)



# def test_exe_section(config):
#     """Verify that the exe section consists of the key-value pairs that were set in an earlier config file
#        (by METplus wrapper code).  We expect to see {'RM':'rm', 'CUT':'cut', 'TR':'tr', 'NCAP2':'ncap2',
#        'CONVERT':'convert', 'NCDUMP':'ncdump'} even though our histo_metplus.conf file has an empty
#        [exe] section.
#     """
#     exe_items = config.items('exe')
#     inherited_exe_items = [('RM','rm'), ('CUT','cut'), ('TR','tr'), ('NCAP2','ncap2'),('CONVERT','convert'), ('NCDUMP','ncdump')]
#     print('exe items: ', exe_items)
#     print("inherited exe items: ", inherited_exe_items)
#
#     # Use the count of tuples in each list of tuples to determine if our lists are
#     # equivalent (have identical number of tuples).
#     .
#     if collections.Counter(inherited_exe_items) == collections.Counter(exe_items):
#         assert True
#     else:
#         assert False
#
#
#
