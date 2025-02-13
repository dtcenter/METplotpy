import pytest

from metplotpy.plots.scatter import scatter
from metplotpy.plots import util

@pytest.skip("plotly generates an html plot-this test cannot be run in a GHA")
def test_scatter(assert_json_equal):
    default_conf_filename = "scatter_defaults.yaml"
    scat = scatter.Scatter(util.get_params("custom_scatter.yaml"),default_conf_filename)
    # Run the following when there is a change in the plot
    scat.figure.write_json('custom_scatter_expected.json')
    assert_json_equal(scat.figure, "custom_scatter_expected.json")


def test_main():
    # check that main can execute without error.
    scatter.main()
    