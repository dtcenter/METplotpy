from metplotpy.plots.scatter import scatter
from metplotpy.plots import util


def test_scatter(assert_json_equal):
    scat = scatter.Scatter(util.get_params("custom_scatter.yaml"))
    assert_json_equal(scat.figure, "custom_scatter_expected.json")
<<<<<<< HEAD


def test_main():
    # check that main can execute without error.
    scatter.main()
=======
>>>>>>> 9d4b43f (461: scatter tests and json compare)
    