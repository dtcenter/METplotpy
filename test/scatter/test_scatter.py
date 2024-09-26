from metplotpy.plots.scatter import scatter
from metplotpy.plots import util


def test_scatter(assert_json_equal):
    scat = scatter.Scatter(util.get_params("custom_scatter.yaml"))
    assert_json_equal(scat.figure, "custom_scatter_expected.json")

