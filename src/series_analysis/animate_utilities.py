"""
 Module to keep various functions that can create animations from static graphics.
"""
import os
import re
import errno
import imageio



def create_gif(duration_secs, files_to_animate, output_filename):
    '''
    Logic modified from the sample code found on the website
       "How To Create GIF Animation with Python"
        http://www.idiotinside.com/2017/06/06/create-gif-animation-with-python

        The original code is for running from the command line and the user does
        not get to chose the output directory and output filename.
        The code example provides a script that reads from the command line the
        duration (seconds) and a whitespace-separated list of png or jpg files
        to include in the gif.  The output gif is saved in the location
        where the command line input was input, and the resulting file has
        the format Gif-YYYY-MM-DD-hh-mm-ss

        In this version, the command line support has been removed and the
        full path to the input png/jpg files is required, along with the duration
        time (in seconds) for each 'frame'.  The output files are located in the
        same output directory specified by the user and the output filename format
        is a variation of the input filename:
        series_<var>_<level_type><level>_<stat>.gif  The filename_regex is used
        to extract the var, level_type, level,
        stat from the input file to create the output filename.

        :param duration_secs:  The time in seconds to view a frame in the animation
        :param files_to_animate: A list of files to animate, the order in which the
                                 files are listed is the order
                                 in which the frames will be ordered in the animation.
        :param output_filename:  The full path filename for the final gif (animation) file.
                                 If the output_dir
        :parm output-dir      :  The directory where the final gif should reside, by default,
                                this is None


    '''

    images = [imageio.imread(filename) for filename in files_to_animate]
    imageio.mimsave(output_filename, images, duration=duration_secs)


def create_gif_from_subset(duration_secs, input_file_dir,
                           input_file_regex, output_filename, output_dir):
    """
        Creates the animation file subsetted from the files in the
        directory where static files are located.  Subsetting is
        performed based on filename pattern.
    :param duration_secs:  The time in seconds to view each frame of
                           the animation
    :param input_file_dir: The full path to the input files
                          (static graphics files in .png or .jpg)
    :param input_file_regex: The regular expression that describes
                             the format of the input files
    :param output_filename: The filename to assign the gif file
                           (without the .gif extension)
    :param output_dir: The directory where the animation file will be saved

    """

    # First, create the output directory if it doesn't exist
    # (equivalent of Unix/Linux 'mkdir -p')
    try:
        os.makedirs(output_dir)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(output_dir):
            pass

    # Check if the user included the .gif extension to the
    # output name.  Add it if not.
    if output_filename.endswith('.gif'):
        full_path_output_filename = os.path.join(output_dir, output_filename)
    else:
        full_path_output_filename = os.path.join(output_dir, output_filename + '.gif')

    files_to_animate = []
    # Retrieve all the files (full filepath) in the input directory
    for root, dirs, files in os.walk(input_file_dir):
        for file in files:
            match = re.match(input_file_regex, file)
            if match:
                files_to_animate.append(os.path.join(input_file_dir, file))

    sorted_files_to_animate = sorted(files_to_animate)


    images = [imageio.imread(filename) for filename in sorted_files_to_animate]
    imageio.mimsave(full_path_output_filename, images, duration=duration_secs)



if __name__ == "__main__":
    # An example for using the create_gif_from_subset() function using
    # the "out of the box" sample data on 'eyewall' (for 'dakota', replace the
    # /d1 directory with the /d4 directory.
    duration = 0.4
    input_file_dir = \
        '/d1/METplus_Plotting_Data/grid_to_grid/201706130000/grid_stat/plots'

    # Subset based on statistic, so for files that look like
    # <var>_DIFF_grid_stat_GFS_vs_ANLYS_hhmmssL_YYYYMMDD_hhmmssV_pairs.png,

    input_file_name_regex = ".*_DIFF.*.png"
    output_dir = \
        '/d1/METplus_Plotting_Data/grid_to_grid/201706130000/grid_stat/plots/animation'

    # The filename (with .gif extension, if it is omitted, then
    # the create_gif_from_subset will add it for you.)
    output_filename = 'TMP_DIFF_all.gif'
    create_gif_from_subset(duration, input_file_dir,
                           input_file_name_regex, output_filename, output_dir)