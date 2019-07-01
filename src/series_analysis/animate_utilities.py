"""
 Module to keep various functions that can create animations from static graphics.
"""
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
        :param output_dir:     The directory where the final gif (animation) file will
                               be saved.
        :param filename_regex:  The regular expression defining the format of the png
                                file from which the final output file will be created.

    '''

    images = [imageio.imread(filename) for filename in files_to_animate]
    imageio.mimsave(output_filename, images, duration=duration_secs)
