import re
import os
import errno
import animate_utilities as au


def animate_series(input_dir):
    '''
    Creates a gif file for a list of png or jpg files


    Creates gif plot containing all png/jpg files in the input_dir for a corresponding var, level, and stat (eg. TMP,
             P500, obar)
    :return:
    '''


def collect_files_to_animate(input_dir, filename_regex, forecast_hours, variable, level_type, level, statistic,
                             animation_duration, is_png=True):
    ''' Collect a list of png/jpg files (the only two formats that are supported by the imageio module)
        that have the same var, level, and stat to include in the gif file.  Files
        will all have the following format: series_Fnnn_[var]_[level]_[stat].png, where
           :param input_dir: The directory where the png/jpg files to be animated are located
           :param filename_regex: The regex describing the format of the input png/jpg file to be included in the
                  animation
           :param forecast_hours:  the list of forecast hours comprising the time frame of the animation
           :param var is the variable: TMP, HGT, etc.
           :param level_type: Level type as indicated by P for pressure level, Z for height above ground, etc
           :param level is the level: 500, 850, etc.
           :param statistic: statistic of interests, either fbar or obar
           :param animation_duration: The amount of time spent on each "frame" of the animation, in seconds.
           :param is_png: flag to indicate if this is a png file or jpg file, by default this is set to True, if
                          files to be animated are jpg, set to False
           Two gif files will be created, one for the specified fhrs, variable, and level for obar statistic
           and the other for the fbar statistic.

           :returns sorted_var_level_stat_paths: a list of png or jpg files based on fhr, variable, level type, level, and statistic,
                         sorted by ascending order

    '''

    # Create all the obar files that will comprise the animation for the obar statistic, filename will look like the
    # following: series_F000_TMP_P850_obar.png, series_F006_TMP_P850_obar.png,...etc. (for all fhrs of interest)
    if is_png:
        extension = ".png"
    else:
        extension = ".jpg"

    var_level_stat_paths = []
    for fhr in forecast_hours:
        # fhr_filepath = os.path.join(input_dir, 'series_' + fhr)
        var_level_stat_filename = 'series_' + fhr + '_' + variable + '_' + level_type + str(
            level) + '_' + statistic + extension
        # var_level_stat_paths.append(os.path.join(fhr_filepath, var_level_stat_filename))
        var_level_stat_paths.append(os.path.join(input_dir, var_level_stat_filename))

    sorted_var_level_stat_paths = sorted(var_level_stat_paths)

    return sorted_var_level_stat_paths

def create_output_filename(output_dir, file_to_animate, filename_regex):
    ''' Create an output file using the directory specified by the user, and based on one of the input files (minus
         the Fxyz portion, hence only one sampe is needed)

         :param output_dir:  The directory where the final gif (animation) file is to be saved
         :param file_to_animate: The name of a png file, to be used to create the .gif output filename.
         :param filename_regex:  The regular expression which defines the format of the png file, used to
                                 create the output gif (animation) file.
    '''

    # filename_regex = "series_F([0-9]{3})_([A-Z]{3})_((P|Z)[0-9]{1,3})_(obar|fbar).png"
    print("file to animate: ", file_to_animate)
    match = re.match(filename_regex, file_to_animate)
    if match:
        variable = match.group(2)
        full_level = match.group(3)
        statistic = match.group(5)

    else:
        raise ValueError(
            "Input file's format does not match expected format, please check the input filename regular expression")

    output_name = "series_" + variable + "_" + full_level + "_" + statistic + ".gif"

    # create the output directory if it doesn't exist (equivalent of mkdir -p)
    try:
        os.makedirs(output_dir)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(output_dir):
            pass
    output_filename = os.path.join(output_dir, output_name)


    return output_filename


if __name__ == "__main__":
    input_dir = "/d1/METplus_Plotting_Data/series_by_lead_all_fhrs/output"
    output_dir = "/d1/METplus_Plotting_Data/series_by_lead_all_fhrs/output/series_animate_python"
    fhrs_list = ["F000", "F006", "F012"]
    variable = "TMP"
    level_type = "P"
    level = "850"
    full_level = level_type + level
    filename_regex = ".*series_F([0-9]{3})_([A-Z]{3})_((P|Z)[0-9]{1,3})_(obar|fbar).png"
    output_gif_base = 'series_'
    animation_duration_secs = 0.8
    statistic = 'obar'
    obar_files = collect_files_to_animate(input_dir, filename_regex, fhrs_list, variable, level_type, level, statistic,
                                          animation_duration_secs)

    #Animate the obar plots
    stat = 'obar'
    # create output filename for obar animation (gif) file
    output_filename = create_output_filename(output_dir, obar_files[0], filename_regex)

    obar_output_gif = au.create_gif(animation_duration_secs, obar_files, output_filename)

    # Animate the fbar plots
    statistic = 'fbar'
    fbar_files = collect_files_to_animate(input_dir, filename_regex, fhrs_list, variable, level_type, level, statistic,
                                          animation_duration_secs)
    # create output filename for fbar animation (gif) file
    output_filename = create_output_filename(output_dir, fbar_files[0], filename_regex)
    fbar_output_gif = au.create_gif(animation_duration_secs, fbar_files, output_filename)



