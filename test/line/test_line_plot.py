import pytest
import os
import yaml
from plots.line.line import Line


@pytest.fixture(scope='module')
def line():
    # Retrieve the contents of the custom config file to over-ride
    # or augment settings defined by the default config file.
    if 'METPLOTPY_BASE' in os.environ:
        location = os.path.join(os.environ['METPLOTPY_BASE'], 'test/line')
    else:
        location = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
    with open(os.path.join(location, 'test_custom_line.yaml'), 'r') as stream:
        try:
            docs = yaml.load(stream, Loader=yaml.FullLoader)
        except yaml.YAMLError as exc:
            print(exc)

    return Line(docs)

def test_config_file(line):
    """
        Verifies that the test_custom_line.yaml config file is read in as
        expected.
        :param line:

    """

    # Test the minimal settings that are
    # required for generating a line plot...
    expected_title = 'Line plot of point data (APCP)'
    lines = line.parameters
    print(lines['title'])
    assert lines['title'] == expected_title

    assert lines['xaxis']['title'] == 'X'
    assert lines['yaxis']['title'] == 'accumulated precip amounts (cm)'


def test_get_all_lines(line):
    """ Verify that all the dictionaries that represent the settings for
        each line/trace in the plot are correctly retrieved.
    """

    # invoke the _get_all_lines() method of the Line class and
    # verify that we are retrieving the values we expect (as
    # defined in the test_custom_line.yaml config file).
    all_lines = line._get_all_lines()
    assert all_lines[0]['name'] == 'Data1 Trace'
    assert all_lines[1]['name'] == 'Data2 Trace'
    assert all_lines[0]['color'] == 'blue'
    assert all_lines[1]['color'] == 'firebrick'
    assert all_lines[0]['width'] == 2
    assert all_lines[1]['width'] == 4
    assert all_lines[0]['dash'] == None
    assert all_lines[1]['dash'] == 'dash'

def test_plot_created(line):
    """ Verify that the line plot is successfully created.
        If there weren't any errors returned while creating the
        plot, then the test passes.
    """

    # Using the fixture, which is based on the settings
    # (and data) specified in the test_custom_line.yaml
    # config file.
    assert (line._create_figure() == None)


