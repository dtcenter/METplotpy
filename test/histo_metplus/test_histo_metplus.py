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

NOTE!!! Use two config files to run these tests, the histogram_defaults.conf file in the 
METplotpy/metplotpy/plots/histogram directory, followed by the histo_metplus.conf file, which
sets the necessary values for the [dir] section required by METplus.    

"""

@pytest.fixture(scope='module')
def config():
    return config_metplus.setup()

## Tests that verify that the config file is correctly processed
def test_metplus_final(config):
    """
          Verify that the metplus_final.conf file was created in the /tmp
          directory.

       """
    assert config

def test_all_sections(config):
    """
       Verify that all the sections retrieved from the config
       file are what we expected.


    """
    all_sections = config.sections()
    expected_sections = ['config', 'dir', 'exe', 'filename_templates', 'regex_pattern',
                         'xaxis', 'yaxis', 'xaxis_title', 'yaxis_title', 'legend', 'xbins']

    for section in all_sections:
        if section not in expected_sections:
            assert False
    else:
        assert True

def test_exe_section(config):
    """Verify that the exe section consists of the key-value pairs that were set in an earlier config file
       (by METplus wrapper code).  We expect to see {'RM':'rm', 'CUT':'cut', 'TR':'tr', 'NCAP2':'ncap2',
       'CONVERT':'convert', 'NCDUMP':'ncdump'} even though our histo_metplus.conf file has an empty
       [exe] section.
    """
    exe_items = config.items('exe')
    inherited_exe_items = [('RM','rm'), ('CUT','cut'), ('TR','tr'), ('NCAP2','ncap2'),('CONVERT','convert'), ('NCDUMP','ncdump')]

    # Use the count of tuples in each list of tuples to determine if our lists are
    # equivalent (have identical number of tuples).

    if collections.Counter(inherited_exe_items) == collections.Counter(exe_items):
        assert True
    else:
        assert False


#
# ## Tests that verify that we are retrieving the values to the key-value pairs in the
# ## INI configuration file
def test_item_of_interest(config):
    """Verify that for a specified section, we are correctly retrieving the

    """
    m = MetPlotIni(config)

    section_of_interest = 'config'
    item_of_interest = 'image_name'
    expected_value = 'histogram'

    value = m.get_config_value(section_of_interest, item_of_interest)

    assert value == expected_value


def test_no_item_of_interest(config):
    """ Verify that we are getting an exception when
        the item_of_interest does not exist
    """
    nonexistant_item = 'foo'
    m = MetPlotIni(config)
    section_of_interest = 'config'
    with pytest.raises(Exception) as e:

       m.get_config_value(section_of_interest, nonexistant_item)
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

       m.get_config_value(nonexistant_section, item_of_interest)
       assert e.value.args[0] == "The section of interest was not found in the configuration file." \
                                 "  Please check your configuration file."


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


def test_get_title(config):
    """ Verify that we are correctly reading the title of the plot, from the
        config section, with the key, 'title'
    """
    m = MetPlotIni(config)
    expected_title = 'Histogram'
    text_dict = m.get_title()
    assert expected_title == text_dict['text']

def test_xaxis(config):
    """Verify that the expected values to keys in the xaxis section
       match what is retrieved via the get_xaxis() method.
    """

    expected_linecolor = 'black'
    expected_showline = 'true'
    expected_linewidth = '2'
    m = MetPlotIni(config)
    axis_dict = m.get_xaxis()
    assert expected_linecolor == axis_dict['linecolor']
    assert expected_showline == axis_dict['showline']
    assert expected_linewidth == axis_dict['linewidth']

def test_yaxis(config):
    """ Verify that the expected values to keys in the yaxis section
        match what is actually retrieved via the get_yaxis() method.
    """

    expected_linecolor = 'black'
    expected_linewidth = '2'
    expected_showline = 'True'
    expected_showgrid = 'True'
    expected_ticks = 'inside'
    expected_tickwidth = '1'
    expected_tickcolor = 'black'
    expected_gridwidth = '1'
    expected_gridcolor = 'rgb(244, 244, 248)'

    m = MetPlotIni(config)
    yaxis_dict = m.get_yaxis()
    assert expected_linecolor == yaxis_dict['linecolor']
    assert expected_linewidth == yaxis_dict['linewidth']
    assert expected_showline == yaxis_dict['showline']
    assert expected_showgrid == yaxis_dict['showgrid']
    assert expected_ticks == yaxis_dict['ticks']
    assert expected_tickwidth == yaxis_dict['tickwidth']
    assert expected_tickcolor == yaxis_dict['tickcolor']
    assert expected_gridwidth == yaxis_dict['gridwidth']
    assert expected_gridcolor == yaxis_dict['gridcolor']


def test_xaxis_title(config):
    """Verify that all the values associated with the xaxis_title are correctly retrieved.
    """
    expected_x = '0.5'
    expected_y = '-0.2'
    expected_showarrow = False
    expected_text = 'x Axis'
    expected_font_family = 'Courier New, monospace'
    expected_font_size = '14'
    expected_font_color = 'Black'
    m = MetPlotIni(config)
    x_axis_title_dict = m.get_xaxis_title()
    assert expected_x == x_axis_title_dict['x']
    assert expected_y == x_axis_title_dict['y']
    assert expected_showarrow == x_axis_title_dict['showarrow']
    assert expected_text == x_axis_title_dict['text']
    assert expected_font_family == x_axis_title_dict['font']['family']
    assert expected_font_size == x_axis_title_dict['font']['size']
    assert expected_font_color == x_axis_title_dict['font']['color']

def test_yaxis_title(config):
    """Verify that all the values associated with the yaxis_title are correctly retrieved.
    """
    expected_x = '0.5'
    expected_y = '-0.2'
    expected_showarrow = False
    expected_text = 'x Axis'
    expected_font_family = 'Courier New, monospace'
    expected_font_size = '14'
    expected_font_color = 'Black'
    m = MetPlotIni(config)
    y_axis_title_dict = m.get_xaxis_title()
    assert expected_x == y_axis_title_dict['x']
    assert expected_y == y_axis_title_dict['y']
    assert expected_showarrow == y_axis_title_dict['showarrow']
    assert expected_text == y_axis_title_dict['text']
    assert expected_font_family == y_axis_title_dict['font']['family']
    assert expected_font_size == y_axis_title_dict['font']['size']
    assert expected_font_color == y_axis_title_dict['font']['color']

@pytest.mark.skip
# skip this test until we figure out how to test this method, which is called recursively
def test_get_nested(config):
    data = {'font': {'family': 'Monospace', 'color':'Blue', 'size':'9'}}
    args = 'font', 'family', 'color', 'size'
    m = MetPlotIni(config)
    m._get_nested(data, args)


# place holder for a test
def test_save_to_file(config):
    """Verifies that the plot is actually saved when requested to save."""
    m = MetPlotIni(config)

    # This method raises exceptions, so if no exceptions are raised, this evaluates
    # to True and passes
    m.save_to_file()
