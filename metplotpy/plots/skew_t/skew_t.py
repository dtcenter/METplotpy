# ============================*
# ** Copyright UCAR (c) 2020
# ** University Corporation for Atmospheric Research (UCAR)
# ** National Center for Atmospheric Research (NCAR)
# ** Research Applications Lab (RAL)
# ** P.O.Box 3000, Boulder, Colorado, 80307-3000, USA
# ============================*

import sys
import pandas as pd
from numpy import log as ln
import math
import matplotlib.pyplot as plt
from metpy.plots import SkewT
from metpy.units import units

"""
  Generate a skew T-log P diagram from TC Diag output
  Currently supports reading in TC Diag ASCII.

"""


def extract_sounding_data(input_file):
    with open(input_file) as infile:
        data = infile.readlines()

    # Identify the lines that bracket the sounding data.
    # The data sections are identified as "STORM DATA", "SOUNDING DATA", and "CUSTOM DATA".
    # Capture the rows of data that fall between the "SOUNDING DATA" header and the "CUSTOM DATA" header.
    for idx, cur in enumerate(data):
        text = cur.split()
        if 'SOUNDING' in text:
            # This is the data we want
            start_line = idx
        if 'CUSTOM' in text:
            end_line = idx

    # Now extract the lines that are in the SOUNDING section.  The first line
    # contains the pressure levels in mb.
    pressure_levels_row: list = data[start_line + 2: start_line + 3]
    # Remove the nlevel and nlevel values from the list
    only_pressure_levels = pressure_levels_row[0].split()
    pressure_levels = only_pressure_levels[3:]
    sounding_data: list = data[start_line + 2: end_line - 1]

    # Save the sounding data into a text file, which will then be converted into a pandas dataframe.
    with open("sounding_data.dat", "w") as txt_file:
        for line in sounding_data:
            txt_file.write("".join(line) + "\n")

    df_raw = pd.read_csv("sounding_data.dat", delim_whitespace=True, skiprows=1)

    # Rename some columns so they are more descriptive
    df = df_raw.rename(columns={'TIME': 'FIELD', '(HR)': 'UNITS'})

    return df, pressure_levels


def extract_sfc_pressures(sounding_data: pd.DataFrame, pressure_levels: list, hour_of_interest: str) -> list:
    ''' From the soundings data, retrieve the surface pressure values and then append the remaining
        pressure values

        Args:
            sounding_data:  The dataframe containing the soundings data of interest.
            pressure_levels:  A list of string values of the pressure levels.  The SURF value will be
                              extracted from the P_SURF field value for each available time of sounding data.
            hour_of_interest:  A string representation of the hour of interest.

        Returns:
            A list of pressures as a dictionary, with each key representing the hour of the sounding data, and
            each corresponding value a list of all the associated pressures.
    '''

    # Store all the pressures in a dictionary, where the keys are the hours and the values are a list of pressure
    # values.  For SURF, read the
    # dataframe and extract the value from the P_SURF row for each time column.
    sfc_pressures_by_hour = {}
    columns = list(df.columns)
    times_list = columns[2:]
    # print ("\n\n Times: ", times_list)

    # Get the location of the surface pressure from the P_SURF row
    psfc_idx: pd.Index = sounding_data.index[df.FIELD == 'P_SURF']
    hours: pd.Series = sounding_data[hour_of_interest]
    pressure: pd.Series = hours.iloc[psfc_idx].values[0]
    # print(pressure.values[0])
    sfc_pressures_by_hour[hour_of_interest] = pressure

    return sfc_pressures_by_hour


def retrieve_pressures(sounding_data: pd.DataFrame, hour_of_interest: str, pressure_levels: list) -> list:
    '''For each hour of interest, create the list of pressures in mb, extracted from the ASCII data. '''

    # First, get the surface pressure level, all the other pressure levels that are above surface level are the same
    sfc_pressure = extract_sfc_pressures(sounding_data, pressure_levels, hour_of_interest)

    # Now retrieve the list of above surface levels (mb) and append these to the sfc_pressure
    all_pressure_levels = pressure_levels.copy()
    all_pressure_levels.insert(0, str(sfc_pressure[hour_of_interest]))

    return all_pressure_levels


def convert_pressures_to_ints(all_pressure_levels: list) -> list:
    ''' Convert the str representation of the pressures into ints so they can be used by Metpy to generate a
        skew T plot.
    '''
    pressures_as_int = [int(level) for level in all_pressure_levels]

    return pressures_as_int


def retrieve_temperatures(sounding_data: pd.DataFrame, hour_of_interest: str, all_pressure_levels: list) -> list:
    '''Retrieve all the temperatures in the soundings dataframe based on pressure level.

       Args:
           sounding_data:  The dataframe containing the sounding data.
           hour_of_interest:  The hour of sounding data.
           all_pressure_levels: A list of all the numerical values of pressure in mb (represented as strings)
       Returns:
           A list of temperature values, corresponding to the pressure level (in mb).
    '''

    # Replace the value for the surface pressure with SURF so we can construct the name of the temperature field.
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


def retrieve_rh(sounding_data: pd.DataFrame, hour_of_interest: str, all_pressure_levels: list) -> list:
    '''Retrieve all the relative humidities in the soundings dataframe based on pressure level.

       Args:
           sounding_data:  The dataframe containing the sounding data.
           hour_of_interest:  The hour of sounding data.
           all_pressure_levels: A list of all the numerical values of pressure in mb (represented as strings)
       Returns:
           A list of relative humidity values, corresponding to the pressure level (in mb).
    '''

    # Replace the value for the surface pressure with SURF so we can construct the name of the temperature field.
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


def retrieve_winds(sounding_data: pd.DataFrame, hour_of_interest: str, all_pressure_levels: list) -> list:
    '''
        Retrieve the u- and v-wind barbs

        Args:
           sounding_data:  The data from the sounding file, represented by a data frame.
           hour_of_interest:  The hour when this sounding was taken.
           all_pressure_levels:  All pressure levels corresponding to this data.

        Returns:
           a list of tuples: u- and v-winds in kts
    '''
    # Replace the value for the surface pressure with SURF so we can construct the name of the temperature field.
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

        # Get the location of the u_wind and v_wind from the u_field row and v_field row, respectively.

        # u-wind
        u_idx: pd.Index = sounding_data.index[sounding_data.FIELD == u_field]
        hours: pd.Series = sounding_data[hour_of_interest]

        # If the field name has been incorrectly formatted, we will observe and IndexError.
        try:
            u_hour: pd.Series = (hours.iloc[u_idx].values[0]) / 10
        except IndexError as ie:
            print("Could not find the field ", u_field,
                  ". Probable cause is incorrectly formatted data. Please check data file.")
            sys.exit()
        u_wind_by_hour.append(u_hour)

        # v-wind
        v_idx: pd.Index = sounding_data.index[sounding_data.FIELD == v_field]

        # If the field name has been incorrectly formatted, we will observe and IndexError.
        try:
            v_hour: pd.Series = (hours.iloc[v_idx].values[0]) / 10

        except IndexError as ie:
            print("Could not find the field ", v_field,
                  ". Probable cause is incorrectly formatted data. Please check data file.")
            sys.exit()
        v_wind_by_hour.append(v_hour)

    return u_wind_by_hour, v_wind_by_hour


def calculate_dewpoint(rh: list, temps: list) -> list:
    from metpy.calc import dewpoint_from_relative_humidity
    from metpy.units import units

    '''
       Calculate the dewpoints from the relative humidities and temperatures using the Magnus-Tetens formula:
       Ts = (b × α(T,RH)) / (a - α(T,RH))

          Where:
          a=17.625
          b=243.04 deg C
          α(T,RH) = ln(RH/100) + aT/(b+T)


       Args:
       rh : a list of relative humidities

       temps: a list of temperatures in degrees Celsius

       Returns:
        A list of dewpoints in degrees Celsius


    '''
    const_a = 17.625
    const_b = 243.04
    zipped = zip(rh, temps)
    dewpts = []
    for idx, cur_vals in enumerate(zipped):
        cur_rh = cur_vals[0]
        cur_temp = cur_vals[1]
        # alpha = (ln(cur_rh/100.) + const_a * cur_temp)/(const_b + cur_temp)
        # divisor = const_b + cur_temp
        # print(f'const_b + cur_temp = {divisor}')
        # natlg = ln(cur_rh/100)
        # print(f'natural humidity = {natlg}, cur_rh= {cur_rh}')
        # calc_dewpoint = (const_b * alpha)/(const_a - alpha)

        if cur_rh == 0:
            dewpoint = np.nan
        else:
            calc_dewpoint = dewpoint_from_relative_humidity(cur_temp * units.degC, cur_rh * units.percent)
            dewpoint = calc_dewpoint.magnitude
        dewpts.append(dewpoint)

    return dewpts


def retrieve_height(sounding_data: pd.DataFrame, hour_of_interest: str, all_pressure_levels: list) -> list:
    '''Retrieve all the hsights (in decameters) in the soundings dataframe based on pressure level.

       Args:
           sounding_data:  The dataframe containing the sounding data.
           hour_of_interest:  The hour of sounding data.
           all_pressure_levels: A list of all the numerical values of pressure in mb (represented as strings)
       Returns:
           A list of heights in meters, corresponding to the pressure level (in mb).
    '''

    # Replace the value for the surface pressure with SURF so we can construct the name of the height field.
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
            except IndexError as ie:
                print("Could not find the field ", hgt_field,
                      ". Probable cause is incorrectly formatted data. Please check data file.")
                sys.exit()
        hgt_by_hour.append(hgt_hour)

    return hgt_by_hour

def create_skew_t(input_file: str) -> None:
    sounding_df, plevs = extract_sounding_data(input_file)

    # For each hour of available sounding data, generate a skew T plot
    columns = list(sounding_df.columns)

    # Limit times to the first few
    times_list = columns[2:6]

    for cur_time in times_list:
        # Retrieve all the pressures
        all_pressure_levels = retrieve_pressures(sounding_df, cur_time, plevs)

        # Convert each pressure to an integer, removing the leading 0's
        pressure = convert_pressures_to_ints(all_pressure_levels)
        # print(pressure_levels_int)

        # Retrieve all the temperatures
        # The first pressure level corresponds to the 'SURF' in the original data file.
        temperature = retrieve_temperatures(sounding_df, cur_time, all_pressure_levels)

        # Retrieve all the relative humidities
        all_rh = retrieve_rh(sounding_df, cur_time, all_pressure_levels)

        # Calculate the dew points
        dew_pt = calculate_dewpoint(all_rh, temperature)
        print(f'dew_points: \n{dew_pt}\n')

        # Wind barbs
        u_winds, v_winds = retrieve_winds(sounding_df, cur_time, all_pressure_levels)

        # Retrieve the heights in meters
        height = retrieve_height(sounding_df, cur_time, all_pressure_levels)

        # Generate plot
        fig = plt.figure(figsize=(9, 9))
        skew = SkewT(fig)
        skew.plot(pressure, temperature, 'r', linewidth=2)
        skew.plot(pressure, dew_pt, 'g', linewidth=2)
        skew.plot_barbs(pressure, u_winds, v_winds)

        # skew.plot_barbs(pressure, u_winds, v_winds)
        skew.plot_dry_adiabats()
        skew.plot_moist_adiabats()
        skew.plot_mixing_lines()
        skew.ax.set_xlim(-35, 40)

        # Add height labels
        decimate = 2
        for p, t, h in zip(pressure[::decimate], temperature[::decimate], height[::decimate]):
            if p >= 100:
                # Heights adjacent to temperature curve.
                # skew.ax.text(t, p, round(h, 0 ))

                # Axis transform to move to x2 axis
                skew.ax.text(1.08, p, round(h, 0), transform=skew.ax.get_yaxis_transform(which='tick2'))
                title = "Skew T for " + input_file + " hour: " + str(cur_time)
        plt.title(title)


if __name__ == "__main__":
    create_skew_t('./2022/al092022/sal092022_avno_doper_2022092200_diag.dat')
