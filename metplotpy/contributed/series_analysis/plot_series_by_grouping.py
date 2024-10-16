# ============================*
 # ** Copyright UCAR (c) 2020
 # ** University Corporation for Atmospheric Research (UCAR)
 # ** National Center for Atmospheric Research (NCAR)
 # ** Research Applications Lab (RAL)
 # ** P.O.Box 3000, Boulder, Colorado, 80307-3000, USA
 # ============================*
 
 
 
"""Generates static plots (png) and animations of those
   plots from netcdf output generated by performing a
   series analysis by grouping.  This script runs
   "out of the box" based on sample input data
   used to run the feature relative use case with
   the series_by_lead_by_fhr_grouping.conf file.
"""

import os, sys
import re
import errno, warnings
import yaml
import matplotlib.pyplot as plt
from matplotlib import cm
import matplotlib.cbook
import cartopy.crs as ccrs
from cartopy.util import add_cyclic_point
import metplotpy.contributed.series_analysis.animate_utilities as au
#pylint: disable=import-error
from netCDF4 import Dataset
sys.path.append("../..")
import metplotpy.plots.util as util
# ignore the MatplotlibFutureDeprecation warning which does not affect this code
# since changes must be made in Cartopy code
warnings.simplefilter(action='ignore', category=matplotlib.cbook.mplDeprecation)



class PlotSeriesByGrouping():
    ''' Generates plots and animations of METplus series analysis by lead
        for grouped data
    '''
    def __init__(self, cfg):
        self.config = cfg

    def create_plots(self, input_dir, output_dir, background_on, filename_regex):
        '''

        :param input_dir:   The input directory where the netcdf files are located.
        :param output_dir:  The output directory where the png files will be saved
        :param background_on: Boolean value to indicate whether to draw coastlines
                              on the plot.
        :param filename_regex: The regular expression of the netcdf file to plot, the
                               Fxxx_to_Fyyy grouping descriptor is
                               needed to include in the plot title to differntiate it
                               from the other groupings.
        :return:
        '''

        # Get the netcdf files in each subdirectory, sorted by grouping name so that
        # Day1 preceeds Day2, and Day2 preceeds Day3, etc.
        nc_files = self.get_nc_files(input_dir)
        # print(nc_files)

        # For each nc_file, read in the necessary values from the netcdf file
        for nc_file in nc_files:
            # print("current nc file: ", nc_file)
            match = re.match(r'.*/(.*).nc', nc_file)
            if match:
                filename_only = match.group(1)

            # Create the output directory if it doesn't already exist
            # create the output directory if it doesn't exist (equivalent of mkdir -p)
            try:
                os.makedirs(output_dir)
            except OSError as exc:
                if exc.errno == errno.EEXIST and os.path.isdir(output_dir):
                    pass
            output_filename = os.path.join(output_dir, filename_only)

            # extract the variable_name and level from the output_filename
            # regex for series by lead groupings:
            # series_(F[0 - 9]{3}_to_F[0 - 9]{3})_([A - Z]{3})_(P | Z)([0 - 9]{1, 3}).*
            filename_only = filename_regex.split('.png')[0]
            filename_only_regex = filename_only + ')'

            var_level_match = re.match(filename_only_regex, output_filename)
            if var_level_match:
                variable_name = var_level_match.group(3)
                level_type = var_level_match.group(4)
                level_name = var_level_match.group(5)
                level = level_type + level_name
            else:
                raise ValueError("The variable and level couldn't be extracted from "
                                 "the netcdf filename.")

            input_nc_file = os.path.join(input_dir, nc_file)

            if input_nc_file.endswith('.nc'):
                try:
                    file_handle = Dataset(input_nc_file, mode='r')
                except FileNotFoundError:
                    print("File ", input_nc_file, " does not exist.")
                else:

                    # Retrieve variables of interest
                    lons = file_handle.variables['lon'][:]
                    lats = file_handle.variables['lat'][:]
                    fbar = file_handle.variables['series_cnt_FBAR'][:]
                    obar = file_handle.variables['series_cnt_OBAR'][:]

                    # close the file handle now that we are finished retrieving what we need
                    file_handle.close()

                # Verify that these values are consistent with lat, lon values, etc.
                # print("lat : ", lats)
                # print("lon : ", lons)
                # print("FBAR: ", fbar)
                # print("OBAR: ", obar)
                # print("===============\n\n")

            # Use the reversed Spectral colormap to reflect temperatures.
            cmap = cm.get_cmap('Spectral_r')

            vars_dict = {'FBAR': fbar, 'OBAR': obar}
            for key, value in vars_dict.items():
                # generate a contour map of OBAR/FBAR values
                plt.figure(figsize=(13, 6.2))
                geo_ax = plt.axes(projection=ccrs.PlateCarree())

                # set number of contour levels to 65, higher number results in more smoothing.
                plt.contourf(lons, lats, value, 65, transform=ccrs.PlateCarree(), cmap=cmap)

                # Only plot the coastlines if the background map is requested
                if background_on:
                    geo_ax.coastlines()

                if key == 'OBAR':
                    var_in_title = "OBAR"
                    # Figure out the minimum and maximum values of the OBAR/FBAR
                    # temperature and use these values in the
                    # plt.Normalize() call.
                    minimum = obar.min()
                    maximum = obar.max()
                    # Allow the temperature values (OBAR, FBAR) and the longitude to
                    # cycle (encircle the globe)
                    # pylint: disable=unused-variable
                    obar_cyc, lon_cyc = add_cyclic_point(obar, coord=lons)
                else:
                    var_in_title = "FBAR"
                    # Figure out the minimum and maximum values of the OBAR/FBAR
                    # temperature and use these values in the
                    # plt.Normalize() call.
                    minimum = fbar.min()
                    maximum = fbar.max()
                    # Allow the temperature values (OBAR, FBAR) and the longitude to cycle
                    # (encircle the globe)
                    # pylint: disable=unused-variable
                    fbar_cyc, lon_cyc = add_cyclic_point(fbar, coord=lons)

                # Adding a legend from Stack Overflow.  Create your own mappable object
                # (scalar mappable) that can be passed to colorbar.  Normalize values
                # are the min and max values normalized to 0, 1 in the
                # solution, here we use the minimum and maximum values found in the
                # FBAR/OBAR array.

                scalar_mappable = plt.cm.ScalarMappable(cmap=cmap, norm=plt.Normalize(minimum, maximum))
                # pylint: disable=protected-access
                scalar_mappable._A = []
                plt.colorbar(scalar_mappable, ax=geo_ax)
                match_group_desc = re.match(filename_only_regex, output_filename)
                if match_group_desc:
                    group_descriptor = match_group_desc.group(2)
                else:
                    raise ValueError("Expecting Fxxx_to_Fyyy info in netcdf "
                                     "filename but info not found... ")

                title = group_descriptor + " for " + var_in_title + " from series by init for " + \
                        variable_name + " " + level
                plt.title(title)

                # output file will be saved as png
                if key == 'OBAR':
                    output_png_file = output_filename + "_obar.png"
                else:
                    output_png_file = output_filename + "_fbar.png"
                # print("output filename: ", output_png_file)
                plt.savefig(output_png_file)

    def get_nc_files(self, input_dir_base):
        '''
            Generate a sorted list (by ascending alphanumeric name) of the netcdf files
            that will be read in to be used for generating plots.
            :param input_dir_base: the base directory where all the input netcdf files
                                   are located
            :return: sorted_nc_files:  A sorted list of the full filepath of the netcdf
                                       files to be used for plotting
        '''
        nc_files = []
        # pylint: disable=unused-variable
        for root, dirs, files in os.walk(input_dir_base):
            for file in files:
                # We only want netcdf files, ignore all other file extensions
                if file.endswith('.nc'):
                    nc_files.append(os.path.join(root, file))

        # sort files by full path in ascending order so Day1 preceeds Day2, and
        # Day3 preceeds Day4...
        sorted_nc_files = sorted(nc_files)
        # print("sorted nc files: ", sorted_nc_files)
        return sorted_nc_files

    def collect_files_to_animate(self, input_dir, statistic):
        '''
        Collect all the files (png) for a given statistic (OBAR or FBAR) to collect in a list.
        :param input_dir: The directory where the png files (plots to be animated) reside.
        :param filename_regex: The regular expression that describes the format of the png files
                              (individual plots).
        :param statistic: The statistic of interest: eg. FBAR or OBAR
        :return: sorted_stat_files: A list of the full path to the files to include in
                                   the animation (gif).
        '''
        stat = statistic.lower()
        stat_files = []
        # pylint: disable=unused-variable
        for root, dirs, files in os.walk(input_dir):
            for file in files:
                if stat == 'obar':
                    match = re.match(r'(.*)_obar.png', file)
                elif stat == 'fbar':
                    match = re.match(r'(.*)_fbar.png', file)
                else:
                    raise ValueError('Statistic ', statistic, ' not supported/recognized.')
                if match:
                    stat_files.append(os.path.join(root, file))

        sorted_stat_files = sorted(stat_files)
        return sorted_stat_files

    def create_output_filename(self, output_dir, file_to_animate, filename_regex):
        '''Create the output filename of the animation file (gif)
           :param output_dir: The directory where the animation file will be saved.
           :param file_to_animate: Provides a sample format of the files to animate.
           :param filename_regex: The regular expression that defines the png files to be animated
           :return output_filename:  The full path and filename of the output animation (gif) file.

        '''

        match = re.match(filename_regex, file_to_animate)
        if match:
            # the 'series_' beginning of the filename
            filename_beginning = match.group(1)

            # The variable_level_stat portion of the filename: eg. TMP_Z2_obar
            var_level_stat = match.group(3)

        else:
            raise ValueError(
                "Input file's format does not match expected format, please check the "
                "input filename regular expression")

        output_name = filename_beginning + "_" + var_level_stat + ".gif"

        # create the output directory if it doesn't exist (equivalent of mkdir -p)
        try:
            os.makedirs(output_dir)
        except OSError as exc:
            if exc.errno == errno.EEXIST and os.path.isdir(output_dir):
                pass
        output_filename = os.path.join(output_dir, output_name)

        return output_filename


def main():
    """
    User sets input values to create_output_filename() and create_gif()
    to generate the static plots (png) and the animations.

    :return:
    """
    config_file = util.read_config_from_command_line()

    with open(config_file, 'r') as stream:
        try:
            config = yaml.load(stream, Loader=yaml.FullLoader)
        except yaml.YAMLError as exc:
            print(exc)

    # Initialize a PlotSeriesByLeadAll instance
    psl = PlotSeriesByGrouping(config)
    input_nc_file_dir = psl.config['input_nc_file_dir']
    output_dir = psl.config['output_dir']

    # Draws coastlines when set to True, by default, this is set to False.
    background_on_setting = psl.config['background_on']
    if background_on_setting.upper() == 'TRUE':
        background_on = True
    else:
        background_on = False

    # Set up regex so we can isolate the filename only (no extension),
    # the grouping descriptor (e.g. the 'Fxxx_to_Fyyy' portion of the netcdf filename),
    # the variable (e.g. TMP, HGT, etc.),
    # the level type : e.g. P or Z, and
    # the level value: e.g. 2, 500, 850, etc.
    filename_regex = psl.config['png_plot_filename_regex']
    psl.create_plots(input_nc_file_dir, output_dir, background_on, filename_regex)

    # duration in sec to stay on each frame in the animation
    duration = psl.config['duration']

    # list of statistics of interest
    statistics_of_interest = psl.config['statistic_of_interest']

    for idx, statistic in enumerate(statistics_of_interest):
        stat_filename_regex = psl.config['stat_filename_regex']
        sorted_stats = psl.collect_files_to_animate(output_dir, statistic)

        # use the first stat in sorted_stats to use as an example to check for correct file format
        # in create_output_filename()
        stat_output_filename = psl.create_output_filename(output_dir, sorted_stats[idx], stat_filename_regex[idx])
        au.create_gif(duration, sorted_stats, stat_output_filename)


if __name__ == "__main__":
    main()
