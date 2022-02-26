# ============================*
 # ** Copyright UCAR (c) 2020
 # ** University Corporation for Atmospheric Research (UCAR)
 # ** National Center for Atmospheric Research (NCAR)
 # ** Research Applications Lab (RAL)
 # ** P.O.Box 3000, Boulder, Colorado, 80307-3000, USA
 # ============================*
 
 
 
"""Creates animation (gif) file of the static plots generated
   from a series analysis by lead for all forecast hours.
"""

import re
import os, sys
import errno
import yaml
sys.path.append("../..")
import metplotpy.contributed.series_analysis.animate_utilities as au
import metplotpy.plots.util as util


class AnimateSeriesByLeadAll():
    def __init__(self,cfg):
        self.config = cfg

    def collect_files_to_animate(self,input_dir, forecast_hours, variable, level_type,
                                 level, statistic):
        ''' Collect a list of png/jpg files (the only two formats that are supported
            by the imageio module) that have the same var, level, and stat to
            include in the gif file.  Files will all have the following format:
            series_Fnnn_[var]_to_Fnnn_[var]_[level]_[stat].png, where
               :param input_dir: The top directory where the png/jpg files to be
                                 animated are located
               :param forecast_hours:  the list of forecast hours comprising the
                                       time frame of the animation
               :param var is the variable: TMP, HGT, etc.
               :param level_type: Level type as indicated by P for pressure level,
                                  Z for height above ground, etc
               :param level is the level: 500, 850, etc.
               :param statistic: statistic of interests, either fbar or obar


               :returns sorted_var_level_stat_paths: a list of png or jpg files based on
                                                     fhr, variable, level type,
                                                     level, and statistic sorted by
                                                     ascending order

        '''

        # Create all the obar files that will comprise the animation for the obar
        # statistic, filename will look like the following:
        # series_F000_TMP_P850_obar.png, series_F006_TMP_P850_obar.png,...etc.
        # (for all fhrs of interest)
        output_format_str = self.config['output_is_png']
        if output_format_str.upper() == 'TRUE':
            extension = ".png"
        else:
            extension = ".jpg"

        var_level_stat_paths = []
        for fhr in forecast_hours:
            # fhr_filepath = os.path.join(input_dir, 'series_' + fhr)
            level_str = str(level)
            var_level_stat_filename = 'series_' + fhr  + '_to_' + fhr + '_' + variable + '_' + level_type + \
                                      level_str + '_' + statistic + extension
            # var_level_stat_paths.append(os.path.join(fhr_filepath, var_level_stat_filename))
            var_level_stat_paths.append(os.path.join(input_dir, var_level_stat_filename))

        sorted_var_level_stat_paths = sorted(var_level_stat_paths)

        return sorted_var_level_stat_paths

    def create_output_filename(self, output_dir, file_to_animate, filename_regex):
        ''' Create an output file using the directory specified by the user, and
             based on one of the input files (minus
             the Fxyz portion, hence only one sample is needed)

             :param output_dir:  The directory where the final gif (animation)
                                 file is to be saved
             :param file_to_animate: The name of a png file, to be used to create
                                     the .gif output filename.
             :param filename_regex:  The regular expression which defines the format
                                     of the png file, used to
                                     create the output gif (animation) file.
        '''

        # filename_regex = "series_F([0-9]{3})_to_F([0-9]{3})_([A-Z]{3})_((P|Z)[0-9]{1,3})_(obar|fbar).png"
        match = re.match(filename_regex, file_to_animate)
        if match:
            variable = match.group(3)
            full_level = match.group(4)
            statistic = match.group(6)

        else:
            raise ValueError(
                "Input file's format does not match expected format, please check the "
                "input filename regular expression")

        output_name = "series_" + variable + "_" + full_level + "_" + \
                      statistic + ".gif"

        # create the output directory if it doesn't exist (equivalent of mkdir -p)
        try:
            os.makedirs(output_dir)
        except OSError as exc:
            if exc.errno == errno.EEXIST and os.path.isdir(output_dir):
                pass
        output_filename = os.path.join(output_dir, output_name)

        return output_filename


def main():
    """Performs animation of static (png) files that were created by plot_series_by_lead_all.
    """
    config_file = util.read_config_from_command_line()

    with open(config_file, 'r') as stream:
        try:
            config = yaml.load(stream, Loader=yaml.FullLoader)
        except yaml.YAMLError as exc:
            print(exc)

    # Initialize a PlotSeriesByLeadAll instance
    asbl = AnimateSeriesByLeadAll(config)



    # Get the values that were set in the yaml config file animate.yaml
    input_dir = asbl.config['input_dir']
    output_dir = asbl.config['output_dir']
    fhrs_list = asbl.config['fhrs_list']
    variable = asbl.config["variable"]
    level_type = asbl.config['level_type']
    level = asbl.config['level']
    filename_regex = asbl.config['filename_regex']
    animation_duration_secs = asbl.config['animation_duration_secs']
    #list of statistics of interest
    statistics_of_interest = asbl.config['statistic_of_interest']

    # Animate the plots corresponding to the statistics of interest for the corresponding forecast, variable, and level
    for statistic in statistics_of_interest:
        stat_files = asbl.collect_files_to_animate(input_dir, fhrs_list, variable,
                                          level_type, level, statistic)
        # create output filename for statistic animation (gif) file
        output_filename = asbl.create_output_filename(output_dir, stat_files[0], filename_regex)
        au.create_gif(animation_duration_secs, stat_files, output_filename)


if __name__ == "__main__":
    main()
