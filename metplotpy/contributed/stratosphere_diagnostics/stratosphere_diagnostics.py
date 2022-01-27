"""
Plotting for Stratosphere diagnostics utilizing Matplotlib, xarray, numpy, and
METplus METcalcpy package (to calculate zonal means and meridional means). Generates the
mean meridional and zonal mean plots for temperature, the zonal mean plot for wind, and a polar cap
meridional mean plot.

Original plotting was provided by Zach Lawrence (CIRES/CU, NOAA/PSL) in the form of a jupyter notebook.
Code was modified to use a configuration file and to be consistent with NCAR's METplotpy code.
 """
__author__ = 'Zach D. Lawrence (CIRES/CU, NOAA/PSL), modified by Minna Win (NCAR)'

import os
import xarray
import xarray as xr
import numpy as np
from matplotlib import pyplot as plt
from metcalcpy.pre_processing.directional_means import meridional_mean
from metcalcpy.pre_processing.directional_means import zonal_mean
import yaml
import errno
from metplotpy.plots import util

def create_output_file(config: dict, plotname: str)->str:
    '''
        Create the output directory where plots are to be saved and then generate the full path and
        filename for the corresponding plot.

        Input:

           :param config: A dictionary representation of the settings in the configuration file.
           :param plotname: The name of the plot to be saved.

        Returns:
        :return: The full filename of the output plot.
    '''

    output_path = config.get('output_plot_path')

    try:
        os.makedirs(output_path)
        return os.path.join(output_path, plotname)

    except OSError as e:
        # do not raise an exception if the directory already exists. Return the full output plot
        # path and name.
        if e.errno == errno.EEXIST:
            return os.path.join(output_path, plotname)
        else:
            raise


def retrieve_data(config: dict) -> xarray.Dataset:
    '''
        Read in all the data from the input data file into an xarray dataset.

        Input:
        :param config: The dictionary representation of the configuration settings

        Returns:
        :return: An xarray dataset representation of the input data of interest
    '''
    data_path = config.get('input_data_path')
    data_filename = config.get('input_datafile')
    input_file = os.path.join(data_path, data_filename)
    full_dataset = xr.open_dataset(input_file)

    # Retrieve the data corresponding to only the variables of interest
    variables = config.get('variables')
    dataset = full_dataset[variables]

    #Rename the variable names from the input data to simpler or more descriptive names
    dataset = dataset.rename({variables[0]: 'time', variables[1]: 'latitude', variables[2]: 'longitude',
                              variables[3]: 'u_wind', variables[4]: 'v_wind', variables[5]: 'temperature',
                              variables[6]: 'level'})
    return dataset



def plot_zonal_mean_wind_contour(config_obj:dict, dataset:xarray.Dataset) -> None:
    '''

        Input:
        :param config_obj: The dictionary representation of settings from the configuration file
        :param dataset: An xarray dataset representation of the input data, subset to only the
                        variables of interest.

        Returns:
        :return: None creates a contour plot of latitude vs atmospheric pressure level of the
                zonal mean wind
    '''

    plt.figure(0)
    output_plotname = config_obj.get('zonal_mean_wind_contour_output_plotname')
    output_plot_file = create_output_file(config_obj, output_plotname)

    u_zonal_mean = zonal_mean(dataset.u_wind)

    time_index = config_obj.get('zonal_mean_wind_contour_time_index')
    contour_start = config_obj.get('zonal_mean_wind_contour_level_start')
    contour_end = config_obj.get('zonal_mean_wind_contour_level_end')
    contour_step = config_obj.get('zonal_mean_wind_contour_level_step_size')
    yscale = config_obj.get('zonal_mean_wind_yscale')

    # Vary the index over time.
    u_zonal_mean.isel(time=time_index).plot.contourf(levels=np.arange(contour_start, contour_end, contour_step))
    plt.gca().invert_yaxis()
    plt.gca().set_yscale(yscale)

    plt.savefig(output_plot_file)

def plot_zonal_mean_temperature_contour(config_obj:dict, dataset:xarray.Dataset) -> None:
    '''

        Input:
        :param config_obj: The dictionary representation of settings from the configuration file
        :param dataset: An xarray dataset representation of the input data, subset to only the
                        variables of interest.

        Returns:
        :return: None creates a contour plot latitude vs atmospheric pressure level of the
                 zonal mean temperature
    '''

    plt.figure(1)
    output_plotname = config_obj.get('zonal_mean_temperature_output_plotname')
    output_plot_file = create_output_file(config_obj, output_plotname)
    time_index = config_obj.get('zonal_mean_temp_contour_time_index')
    contour_start = config_obj.get('zonal_mean_temp_contour_level_start')
    contour_end = config_obj.get('zonal_mean_temp_contour_level_end')
    contour_step = config_obj.get('zonal_mean_temp_contour_level_step_size')
    yscale = config_obj.get('zonal_mean_temp_yscale')

    temperature_zonal_mean = zonal_mean(dataset.temperature)
    temperature_zonal_mean.isel(time=time_index).plot.contourf(
        levels=np.arange(contour_start, contour_end, contour_step))
    plt.gca().invert_yaxis()
    plt.gca().set_yscale(yscale)

    plt.savefig(output_plot_file)


def plot_zonal_mean_wind(config_obj:dict, dataset:xarray.Dataset) -> None:
    '''

        Input:
        :param config_obj: The dictionary representation of settings from the configuration file
        :param dataset: An xarray dataset representation of the input data, subset to only the
                        variables of interest.

        Returns:
        :return: None creates a contour plot latitude vs atmospheric pressure level of the
                 zonal mean wind.
    '''

    plt.figure(2)
    output_plotname = config_obj.get('zonal_mean_wind_output_plotname')
    output_plot_file = create_output_file(config_obj, output_plotname)
    zm_latitude = config_obj.get('zonal_mean_wind_latitude')
    pressure = config_obj.get('zonal_mean_wind_pressure_hpa')
    u_wind_zonal_mean = zonal_mean(dataset.u_wind)
    u_wind_zonal_mean.sel(latitude=zm_latitude, pres=pressure).plot()

    plt.savefig(output_plot_file)


def plot_polar_zonal_mean_temperature(config_obj:dict, dataset:xarray.Dataset) -> None:
    '''

        Input:
        :param config_obj: The dictionary representation of settings from the configuration file
        :param dataset: An xarray dataset representation of the input data, subset to only the
                        variables of interest.

        Returns:
        :return: None creates a contour plot latitude vs atmospheric pressure level of the
                 zonal mean wind.
    '''

    plt.figure(3)
    output_plotname = config_obj.get('polar_cap_meridional_mean_temp_output_plotname')
    output_plot_file = create_output_file(config_obj, output_plotname)
    temperature_zonal_mean = zonal_mean(dataset.temperature)
    start_lat = config_obj.get('polar_cap_lat_start')
    end_lat = config_obj.get('polar_cap_lat_end')
    pressure_hp = config_obj.get('polar_cap_pressure_hpa')
    # polar cap average of temperatures from latitudes specified in the configuration file
    polar_temp = meridional_mean(temperature_zonal_mean, start_lat, end_lat)
    polar_temp.sel(pres=pressure_hp).plot()
    plt.savefig(output_plot_file)

def main(config_filename=None):
    # Retrieve the contents of the config file
    if not config_filename:
        config_file = util.read_config_from_command_line()
    else:
        config_file = config_filename
    with open(config_file, 'r') as stream:
        try:
            config = yaml.load(stream, Loader=yaml.FullLoader)
        except yaml.YAMLError as exc:
            print(exc)

    try:
        # do any preparations
        dataset = retrieve_data(config)

        # generate the plots
        # plot_zonal_mean_wind_contour(config, dataset)
        # plot_zonal_mean_temperature_contour(config, dataset)
        plot_zonal_mean_wind(config, dataset)
        plot_polar_zonal_mean_temperature(config, dataset)
    except ValueError as val_er:
        print(val_er)


if __name__ == "__main__":
    main()