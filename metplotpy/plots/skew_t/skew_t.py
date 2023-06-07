# ============================*
# ** Copyright UCAR (c) 2020
# ** University Corporation for Atmospheric Research (UCAR)
# ** National Center for Atmospheric Research (NCAR)
# ** Research Applications Lab (RAL)
# ** P.O.Box 3000, Boulder, Colorado, 80307-3000, USA
# ============================*

import sys
import os
import re
import logging
import warnings
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from metpy.plots import SkewT
import yaml

from metplotpy.plots import util

logger = logging.getLogger(__name__)
# Suppress debug messages from Matplotlib
logging.getLogger(name='matplotlib').setLevel(logging.ERROR)

"""
  Generate a skew T-log P diagram from TC Diag output
  Currently supports reading in TC Diag ASCII.

"""

# Suppress the UserWarning generated by Metpy skewt.py: "color is redundantly defined
# by the 'color' keyword argument..."  There is no workaround.
warnings.filterwarnings(action='ignore', category=UserWarning)


def extract_sounding_data(input_file):
    with open(input_file) as infile:
        data = infile.readlines()

    # Identify the lines that bracket the sounding data.
    # The data sections are identified as "STORM DATA", "SOUNDING DATA", and "CUSTOM
    # DATA".
    # Capture the rows of data that fall between the "SOUNDING DATA" header and the
    # "CUSTOM DATA" header.
    for idx, cur in enumerate(data):
        text = cur.split()
        if 'SOUNDING' in text:
            # This is the data we want
            start_line = idx
        if 'CUSTOM' in text:
            end_line = idx

    # Now extract the lines that are in the SOUNDING section.  The first line
    # contains the pressure levels in mb.
    pressure_levels_row:list = data[start_line + 2: start_line + 3]
    # Remove the nlevel and nlevel values from the list
    only_pressure_levels = pressure_levels_row[0].split()
    pressure_levels = only_pressure_levels[3:]
    sounding_data:list = data[start_line + 2: end_line - 1]

    # Save the sounding data into a text file, which will then be converted into a
    # pandas dataframe.
    with open("sounding_data.dat", "w") as txt_file:
        for line in sounding_data:
            txt_file.write("".join(line) + "\n")

    df_raw = pd.read_csv("sounding_data.dat", delim_whitespace=True, skiprows=1)

    # Rename some columns so they are more descriptive
    df = df_raw.rename(columns={'TIME': 'FIELD', '(HR)': 'UNITS'})

    return df, pressure_levels


def retrieve_date_and_basin(input_file) -> tuple:
    ''' Retrieve the yyyymmdd date and basin and storm id eg AL## from the first
        two lines of the data file.

        Args:
           input_file:  The ASCII input file

        Returns:
           a tuple of strings:  the first is the yyyymdd date, followed by the basin
           and storm id.
    '''

    with open(input_file) as infile:
        data = infile.readlines()
        for idx, cur in enumerate(data):
            if idx == 0:
                ymd_string = cur
            elif idx == 1:
                basin_stormid_str = cur

    ymd = re.match(r'(.*)(\d{10})', ymd_string)
    if ymd:
        ymd_date = ymd.group(2)

    basin_storm = re.match(r'(.*)(\w{4})', basin_stormid_str)
    if basin_storm:
        basin_storm_info = basin_storm.group(2)

    return ymd_date, basin_storm_info


def retrieve_units(sounding_data: pd.DataFrame) -> dict:
    '''
       Retrieve the units from the ASCII file.

       Args:
          sounding_data:  The pandas dataframe containing the sounding data.

       Returns:
         units: a dictionary of the field as key and units as value (where the
         parenthesis
                are removed from the unit descriptor).
    '''

    fields_str = sounding_data.FIELD
    units = {}

    # Get the units for the field (use the surface level, so we can capture the
    # Pressure units).
    # Also get the Z_1000 to get the height, as there is no Z_SURF field.
    for cur_field in fields_str:
        level_str = re.match(r'(Z)_1000', cur_field)
        field_level_str = re.match(r'(\w)_SURF', cur_field)
        if level_str:
            field_level_str = level_str
        if field_level_str:
            field_name = field_level_str.group(1)

            units_str_series: pd.Series = (
                (sounding_data.loc[sounding_data.FIELD == cur_field]).UNITS)
            units_str = units_str_series.iloc[0]

            # Clean up the enclosing parenthesis
            unit: list = re.findall(r"\((.*?)\)", units_str)
            units[field_name] = unit[0]

    return units


def extract_sfc_pressures(sounding_data: pd.DataFrame,
                          hour_of_interest: str) -> dict:
    ''' From the soundings data, retrieve the surface pressure values and then append
    the remaining
        pressure values

        Args:
            sounding_data:  The dataframe containing the soundings data of interest.
            hour_of_interest:  A string representation of the hour of interest.

        Returns:
            A list of pressures as a dictionary, with each key representing the hour
            of the sounding data, and
            each corresponding value a list of all the associated pressures.
    '''

    # Store all the pressures in a dictionary, where the keys are the hours and the
    # values are a list of pressure
    # values.  For SURF, read the
    # dataframe and extract the value from the P_SURF row for each time column.
    sfc_pressures_by_hour = {}
    columns = list(sounding_data.columns)
    columns[2:]

    # Get the location of the surface pressure from the P_SURF row
    psfc_idx: pd.Index = sounding_data.index[sounding_data.FIELD == 'P_SURF']
    hours: pd.Series = sounding_data[hour_of_interest]
    pressure: pd.Series = hours.iloc[psfc_idx].values[0]
    # (pressure.values[0])
    sfc_pressures_by_hour[hour_of_interest] = pressure

    return sfc_pressures_by_hour


def retrieve_pressures(sounding_data: pd.DataFrame, hour_of_interest: str,
                       pressure_levels: list) -> list:
    '''For each hour of interest, create the list of pressures in mb, extracted from
    the ASCII data.

     Args:
           sounding_data:  The dataframe containing the sounding data.
           hour_of_interest:  The hour of sounding data.
           all_pressure_levels: A list of all the numerical values of pressure in mb
           (represented as strings)

    '''

    # First, get the surface pressure level, all the other pressure levels that are
    # above surface level are the same
    sfc_pressure = extract_sfc_pressures(sounding_data, hour_of_interest)

    # Now retrieve the list of above surface levels (mb) and append these to the
    # sfc_pressure
    all_pressure_levels = pressure_levels.copy()
    all_pressure_levels.insert(0, str(sfc_pressure[hour_of_interest]))

    return all_pressure_levels


def convert_pressures_to_ints(all_pressure_levels: list) -> list:
    ''' Convert the str representation of the pressures into ints so they can be used
    by Metpy to generate a
        skew T plot.

         Args:
           sounding_data:  The dataframe containing the sounding data.
           hour_of_interest:  The hour of sounding data.
           all_pressure_levels: A list of all the numerical values of pressure in mb
           (represented as strings)
    '''
    pressures_as_int = [int(level) for level in all_pressure_levels]

    return pressures_as_int


def retrieve_temperatures(sounding_data: pd.DataFrame, hour_of_interest: str,
                          all_pressure_levels: list) -> list:
    '''Retrieve all the temperatures in the soundings dataframe based on pressure level.

       Args:
           sounding_data:  The dataframe containing the sounding data.
           hour_of_interest:  The hour of sounding data.
           all_pressure_levels: A list of all the numerical values of pressure in mb
           (represented as strings)
       Returns:
           A list of temperature values, corresponding to the pressure level (in mb).
    '''

    # Replace the value for the surface pressure with SURF so we can construct the
    # name of the temperature field.
    above_sfc = all_pressure_levels[1:]
    plevs = above_sfc.copy()
    plevs.insert(0, 'SURF')

    temperatures_by_hour = []
    for cur_lev in plevs:
        # Create the string describing the pressure levels
        temp_prefix = 'T_'
        temp_field = temp_prefix + cur_lev

        # Get the location of the temperature from the temp_field row.
        temp_idx: pd.Index = sounding_data.index[sounding_data.FIELD == temp_field]
        hours: pd.Series = sounding_data[hour_of_interest]
        temp_hour: pd.Series = hours.iloc[temp_idx].values[0]
        # Temperatures need to be divie by 10 since units are 10C
        temperatures_by_hour.append(temp_hour / 10)

    return temperatures_by_hour


def retrieve_rh(sounding_data: pd.DataFrame, hour_of_interest: str,
                all_pressure_levels: list) -> list:
    '''Retrieve all the relative humidities in the soundings dataframe based on
    pressure level.

       Args:
           sounding_data:  The dataframe containing the sounding data.
           hour_of_interest:  The hour of sounding data.
           all_pressure_levels: A list of all the numerical values of pressure in mb
           (represented as strings)
       Returns:
           A list of relative humidity values, corresponding to the pressure level (
           in mb).
    '''

    # Replace the value for the surface pressure with SURF so we can construct the
    # name of the temperature field.
    above_sfc = all_pressure_levels[1:]
    plevs = above_sfc.copy()
    plevs.insert(0, 'SURF')

    rh_by_hour = []
    for cur_lev in plevs:
        # Create the string describing the pressure levels
        rh_prefix = 'R_'
        rh_field = rh_prefix + cur_lev

        # Get the location of the rh from the rh_field row.
        rh_idx: pd.Index = sounding_data.index[sounding_data.FIELD == rh_field]
        hours: pd.Series = sounding_data[hour_of_interest]
        rh_hour: pd.Series = hours.iloc[rh_idx].values[0]
        rh_by_hour.append(rh_hour)

    return rh_by_hour


def retrieve_winds(sounding_data: pd.DataFrame, hour_of_interest: str,
                   all_pressure_levels: list) -> tuple:
    '''
        Retrieve the u- and v-wind barbs

        Args:
           sounding_data:  The data from the sounding file, represented by a data frame.
           hour_of_interest:  The hour when this sounding was taken.
           all_pressure_levels:  All pressure levels corresponding to this data.

        Returns:
           a tuple of lists: u- and v-winds in kts
    '''
    # Replace the value for the surface pressure with SURF so we can construct the
    # name of the temperature field.
    above_sfc = all_pressure_levels[1:]
    plevs = above_sfc.copy()
    plevs.insert(0, 'SURF')

    u_wind_by_hour = []
    v_wind_by_hour = []
    for cur_lev in plevs:
        # Create the string describing the pressure levels
        u_prefix = 'U_'
        v_prefix = 'V_'
        u_field = u_prefix + cur_lev
        v_field = v_prefix + cur_lev

        # Get the location of the u_wind and v_wind from the u_field row and v_field
        # row, respectively.

        # u-wind
        u_idx: pd.Index = sounding_data.index[sounding_data.FIELD == u_field]
        hours: pd.Series = sounding_data[hour_of_interest]

        # If the field name has been incorrectly formatted, we will observe and
        # IndexError.
        error_msg_1 = "Could not find the field"
        error_msg_2 = "Probable cause is incorrectly formatted data. Please check the " \
                      "data file"
        try:
            u_hour: pd.Series = (hours.iloc[u_idx].values[0]) / 10
        except IndexError:
            logger.error(f"Index Error: {error_msg_1} {u_field}, {error_msg_2}")
            sys.exit()
        u_wind_by_hour.append(u_hour)

        # v-wind
        v_idx: pd.Index = sounding_data.index[sounding_data.FIELD == v_field]

        # If the field name has been incorrectly formatted, we will observe and
        # IndexError.
        try:
            v_hour: pd.Series = (hours.iloc[v_idx].values[0]) / 10

        except IndexError:
            error_msg = error_msg_1 + error_msg_2
            logger.error(f"Index Error: {error_msg}")
            sys.exit()
        v_wind_by_hour.append(v_hour)

    return u_wind_by_hour, v_wind_by_hour


def calculate_dewpoint(rh: list, temps: list) -> list:
    from metpy.calc import dewpoint_from_relative_humidity
    from metpy.units import units

    '''
       Calculate the dewpoints from the relative humidities and temperatures.

       Args:
       rh : a list of relative humidities

       temps: a list of temperatures in degrees Celsius

       Returns:
        A list of dewpoints in degrees Celsius


    '''
    zipped = zip(rh, temps)
    dewpts = []
    for idx, cur_vals in enumerate(zipped):
        cur_rh = cur_vals[0]
        cur_temp = cur_vals[1]

        if cur_rh == 0:
            dewpoint = np.nan
        else:
            calc_dewpoint = dewpoint_from_relative_humidity(cur_temp * units.degC,
                                                            cur_rh * units.percent)
            dewpoint = calc_dewpoint.magnitude
        dewpts.append(dewpoint)

    return dewpts


def retrieve_height(sounding_data: pd.DataFrame, hour_of_interest: str,
                    all_pressure_levels: list) -> list:
    '''Retrieve all the hsights (in decameters) in the soundings dataframe based on
    pressure level.

       Args:
           sounding_data:  The dataframe containing the sounding data.
           hour_of_interest:  The hour of sounding data.
           all_pressure_levels: A list of all the numerical values of pressure in mb
           (represented as strings)
       Returns:
           A list of heights in meters, corresponding to the pressure level (in mb).
    '''

    # Replace the value for the surface pressure with SURF so we can construct the name
    # of the height field.
    above_sfc = all_pressure_levels[1:]
    plevs = above_sfc.copy()
    plevs.insert(0, 'SURF')
    hgt_by_hour = []

    for cur_lev in plevs:
        # Create the string describing the pressure levels
        hgt_prefix = 'Z_'
        hgt_field = hgt_prefix + cur_lev

        # Get the location of the height from the hgt_field row.
        hgt_idx: pd.Index = sounding_data.index[sounding_data.FIELD == hgt_field]
        hours: pd.Series = sounding_data[hour_of_interest]
        # Convert from decameters to meters

        #  Make special accomodation for no Z_SURF, which is just 0
        if hgt_field == 'Z_SURF':
            hgt_hour = 0
        else:
            try:

                hgt_hour: pd.Series = (hours.iloc[hgt_idx].values[0]) * 10
            except IndexError:
                logger.error(f"IndexError: Could not find field  {hgt_field}.  "
                             f"Probably due to incorrectly formatted or unexpected "
                             f"formatting of data.")
                sys.exit()
        hgt_by_hour.append(hgt_hour)

    return hgt_by_hour


def create_skew_t(input_file: str, config: dict) -> None:
    '''

      Create a skew T diagram from the TC Diag output.

      Args:
          input_file: The input file of interest.  Generate skew T plots for
                      all the sounding hours of interest (or all hours), as
                      indicated in the configuration file.
          config:  A dictionary representation of the settings and their values
                   in the configuration file.

     Return:
           None, generate plots as png files in the specified output file directory.
    '''
    logger.info(f" Creating skew T plots for input file {input_file} ")
    sounding_df, plevs = extract_sounding_data(input_file)

    # For each hour of available sounding data, generate a skew T plot.
    # Each column contains all the sounding data for a particular hour 0-240
    columns = list(sounding_df.columns)

    date_ymdh, basin_storm = retrieve_date_and_basin(input_file)

    # Limit times to those specified in the configuration file.
    if config['all_sounding_hours']:
        # Columns 0-1 are Field names and their units.
        times_list = columns[2:]
    else:
        times_list_config = config['sounding_hours_of_interest']
        # Convert integers into strings in the event that the user indicated
        # integers in the config file  instead of strings for the hours of interest.
        times_list = [str(cur_time) for cur_time in times_list_config]

    for cur_time in times_list:
        # Retrieve all the pressures
        all_pressure_levels = retrieve_pressures(sounding_df, cur_time, plevs)

        # Convert each pressure to an integer, removing the leading 0's
        pressure = convert_pressures_to_ints(all_pressure_levels)

        # Retrieve all the temperatures
        # The first pressure level corresponds to the 'SURF' in the original data file.
        temperature = retrieve_temperatures(sounding_df, cur_time, all_pressure_levels)

        # Retrieve all the relative humidities
        all_rh = retrieve_rh(sounding_df, cur_time, all_pressure_levels)

        # Calculate the dew points
        dew_pt = calculate_dewpoint(all_rh, temperature)

        # Wind barbs
        u_winds, v_winds = retrieve_winds(sounding_df, cur_time, all_pressure_levels)

        # Retrieve the heights in meters
        height = retrieve_height(sounding_df, cur_time, all_pressure_levels)

        # Generate plot
        fig_width = config['figure_size_width']
        fig_height = config['figure_size_height']
        fig = plt.figure(figsize=(fig_width, fig_height))
        skew = SkewT(fig)

        temp_linewidth = config['temp_line_thickness']
        temp_linestyle = config['temp_line_style']
        temp_linecolor = config['temp_line_color']
        skew.plot(pressure, temperature, 'r', linewidth=temp_linewidth,
                  linestyle=temp_linestyle, color=temp_linecolor)

        dewpt_linewidth = config['dewpt_line_thickness']
        dewpt_linestyle = config['dewpt_line_style']
        dewpt_linecolor = config['dewpt_line_color']
        skew.plot(pressure, dew_pt, 'g', linewidth=dewpt_linewidth,
                  linestyle=dewpt_linestyle, color=dewpt_linecolor)

        # Adiabat and mixing lines.
        if config['display_dry_adiabats']:
            skew.plot_dry_adiabats()
        if config['display_moist_adiabats']:
            skew.plot_moist_adiabats()
        if config['display_mixing_lines']:
            skew.plot_mixing_lines()

        # Wind barbs
        # Resampling the windbarbs by getting the decimate_barbs value.
        # Sample only every nth wind barb.  If decimate = 1, no resampling
        # will be performed and the original number of available windbarbs will
        # be plotted.
        decimate = config['decimate_barbs']

        if config['display_windbarbs']:
            skew.plot_barbs(pressure[::decimate], u_winds[::decimate], v_winds[
                ::decimate])

        # Add height labels

        for p, t, h in zip(pressure[::decimate], temperature[::decimate],
                           height[::decimate]):
            # Masking to only plot wind barbs and pressures that are >= 100 hPa
            if p >= 100:
                # Heights adjacent to temperature curve. Either along the y2 axis
                # or next to the temperature curve
                if config['level_labels_along_y2-axis']:
                    # Axis transform to move to y2 axis
                    skew.ax.text(1.08, p, round(h, 0),
                                 transform=skew.ax.get_yaxis_transform(which='tick2'))

                else:
                    skew.ax.text(t, p, round(h, 0))

                title = "Skew T for " + date_ymdh + " " + basin_storm + " hour: " \
                        + str(cur_time)

        # Focus in on curves to eliminate "white space" in plot.
        if config['set_x_axis_limits']:
            x_axis_min = config['x_axis_min']
            x_axis_max = config['x_axis_max']
            skew.ax.set_xlim(x_axis_min, x_axis_max)

        plt.title(title)

        # Save the plots/figures in the output directory as specified, using
        # the same name as the input file, appending the hour of the sounding to
        # the data file name, then replacing the datat file extension
        # with '.png'.

        # Create the plot files in the output directory specified in the config
        # file.
        output_dir = config['output_directory']
        try:
            os.mkdir(output_dir)
        except FileExistsError:
            # Ignore if file/diretory already exists, this is OK.
            pass
        full_filename_only, _ = os.path.splitext(input_file)
        filename_only = os.path.basename(full_filename_only)
        renamed = filename_only + "_" + cur_time + "_hr.png"
        plot_file = os.path.join(output_dir, renamed)
        logging.info(f"saving file {plot_file}")

        plt.savefig(plot_file)

        # plt.show()


def main(config_filename=None):
    '''
       Entry point for generating a skewT diagram from the command line.

       Args:

       Returns:

    '''
    if not config_filename:
        config_file = util.read_config_from_command_line()
    else:
        config_file = config_filename
    with open(config_file, 'r') as stream:
        try:
            config = yaml.load(stream, Loader=yaml.FullLoader)

            # Set up the logging.
            log_dir = config['log_directory']
            log_file = config['log_filename']
            log_full_path = os.path.join(log_dir, log_file)
            try:
                os.mkdir(log_dir)
            except FileExistsError:
                # If directory already exists, this is OK.  Continue.
                pass

            log_level = config['log_level']
            format_str = "'%(asctime)s||%(levelname)s||%(funcName)s||%(message)s'"
            if log_level == 'DEBUG':
                logging.basicConfig(filename=log_full_path, level=logging.DEBUG,
                                    format=format_str,
                                    filemode='w')
            elif log_level == 'INFO':
                logging.basicConfig(filename=log_full_path, level=logging.INFO,
                                    format=format_str,
                                    filemode='w')
            elif log_level == 'WARNING':
                logging.basicConfig(filename=log_full_path, level=logging.WARNING,
                                    format=format_str,
                                    filemode='w')
            else:
                # log_level == 'ERROR'
                logging.basicConfig(filename=log_full_path, level=logging.ERROR,
                                    format=format_str,
                                    filemode='w')

            # Get the list of input files to visualize.
            input_dir = config['input_directory']
            file_ext = config['input_file_extension']
            for root, dir, files in os.walk(input_dir):
                all_files = [file for file in files if file.endswith(file_ext)]
                files_of_interest = [os.path.join(root, file) for file in all_files]

            # Create skew T diagrams for each input file.
            for file_of_interest in files_of_interest:
                create_skew_t(file_of_interest, config)

            # create_skew_t(input_file, config)
        except yaml.YAMLError as exc:
            logger.error(f"YAMLError: {exc}")


if __name__ == "__main__":
    main()
