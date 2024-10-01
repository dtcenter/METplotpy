from metplotpy.plots.scatter import scatter
from metplotpy.plots import util


def test_scatter(assert_json_equal):
    default_conf_filename = "scatter_defaults.yaml"
    scat = scatter.Scatter(util.get_params("custom_scatter.yaml"),default_conf_filename)
    assert_json_equal(scat.figure, "custom_scatter_expected.json")


def test_main():
    # check that main can execute without error.
    scatter.main()
