"""Tests used to establish the expected behavior of the plotting histogram.
"""

import numpy as np
import pytest

from metplotpy.plots.histogram.histogram import Histogram


def test_histogram_show_in_browser():
    first_marker = np.random.randn(500)
    second_marker = np.random.randn(500) + 1
    data = []
    data.append(first_marker)
    data.append(second_marker)
    histogram = Histogram(None, data)
    assert histogram.get_yaxis_title()['text'] == 'y Axis'
    histogram.show_in_browser()


def test_get_settings(settings):
    assert settings.figure._data[0]['marker']['color'] == 'white'
    assert settings.figure._layout['annotations'][1]['text'] == 'y Axis'
    assert settings.figure._data[0]['name'] == 'Series 1'


@pytest.fixture
def settings():
    """Initialise values for testing.

    Returns:
        dictionary with values of different type
    """
    first_marker = np.random.randn(500)
    second_marker = np.random.randn(500) + 1
    data = [first_marker, second_marker]
    histogram = Histogram(None, data)
    return histogram


def test_get_array_dimensions():
    data = None
    assert Histogram.get_array_dimensions(data) is None

    first_marker = np.random.randn(500)
    second_marker = np.random.randn(500) + 1
    assert Histogram.get_array_dimensions(first_marker) == 1

    data = [first_marker, second_marker]
    assert Histogram.get_array_dimensions(data) == 2


if __name__ == "__main__":
    test_get_array_dimensions()
    test_histogram_show_in_browser()

