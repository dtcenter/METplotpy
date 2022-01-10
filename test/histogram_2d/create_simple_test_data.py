import numpy as np
import xarray as xr


def create_test_data(filename_in):
    """
        Generate simple dataset for the histogram_2d plot
    :param filename_in: the full filename (path + filename) that will be assigned to the test data
    :return:
    """
    print('Creating test data')
    nx, ny = 21, 21
    x_coord = np.linspace(-2, 2, nx)
    y_coord = np.linspace(-2, 2, ny)
    x_mesh, y_mesh = np.meshgrid(x_coord, y_coord, indexing='ij')
    f_mesh = 4 - np.square(x_mesh - y_mesh + 1)
    f_mesh = np.clip(f_mesh, 0, 4)
    f_array = xr.DataArray(f_mesh,
                           dims=['x', 'y'],
                           coords={'x': x_coord, 'y': y_coord})
    ds = xr.Dataset({'hist_x_y': f_array})
    ds.to_netcdf(filename_in)

if __name__ == "__main__":
    test_data_filename = "./test_histogram_2d_data.nc"
    create_test_data(test_data_filename)