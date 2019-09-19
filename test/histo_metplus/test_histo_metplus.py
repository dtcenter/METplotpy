import os.path
import sys
import collections
import pytest
import config_metplus
import histo_metplus
from met_plot_ini import MetPlotIni


"""
Tests for the METplotpy configuration file parsing and retrieval of values to conform to the Plotly dictionaries
needed to generate plots.

"""

@pytest.fixture(scope='module')
def config():
    return config_metplus.setup()

## Tests that verify that the config file is correctly processed
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
#     expected_sections = ['config', 'dir', 'exe', 'filename_templates', 'regex_pattern',
#                          'xaxis', 'yaxis', 'xaxis_title', 'yaxis_title', 'legend', 'xbins']
#
#     for section in all_sections:
#         print('Current section found: ', section)
#         if section not in expected_sections:
#             assert False
#     else:
#         assert True
#
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
#
#     if collections.Counter(inherited_exe_items) == collections.Counter(exe_items):
#         assert True
#     else:
#         assert False
#


## Tests that verify that we are retrieving the values to the key-value pairs in the
## INI configuration file
def test_item_of_interest(config):
    """Verify that for a specified section, we are correctly retrieving the

    """
    m = MetPlotIni(config)

    section_of_interest = 'config'
    item_of_interest = 'image_name'
    expected_value = 'histogram'

    value = m.get_item_value(section_of_interest, item_of_interest)

    assert value == expected_value

def test_no_item_of_interest(config):
    """ Verify that we are getting an exception when
        the item_of_interest does not exist
    """
    nonexistant_item = 'foo'
    m = MetPlotIni(config)
    section_of_interest = 'config'
    with pytest.raises(Exception) as e:

       m.get_item_value(section_of_interest, nonexistant_item)
       assert e.value.args[0] == "The item of interest was not found in the configuration file.  Please check your configuration file."


def test_no_section_of_interest(config):
    """ Verify that we are getting an exception when
        the section_of_interest does not exist
    """
    nonexistant_section = 'foo'
    item_of_interest = 'image_name'
    m = MetPlotIni(config)
    section_of_interest = 'config'
    with pytest.raises(Exception) as e:

       m.get_item_value(nonexistant_section, item_of_interest)
       assert e.value.args[0] == "The section of interest was not found in the configuration file.  Please check your configuration file."


def test_get_image_format(config):
    """ Verify that the expected image format is getting retrieved from the config file. Specifically from the
        key 'image_name'.  The image format returned should be .png since we didn't indicate this in the
        image_name value, and the default format should be returned whenever it is not explicitly indicated in
        the config file.


    """
    expected_fmt = 'png'
    m = MetPlotIni(config)
    assert expected_fmt == m.get_image_format()

def test_get_image_format_jpeg(config):
    """ Verify that when the image_name is set to something with a .jpeg
        extension, the appropriate format, 'jpeg' is returned.

    """

    # set the image_name to 'bar.jpeg' in the parameters/configuration object so we
    # don't have to use a different configuration file to run this test.
    config.set('config', 'image_name', 'bar.jpeg')
    m = MetPlotIni(config)
    expected_fmt = 'jpeg'
    assert expected_fmt == m.get_image_format()


