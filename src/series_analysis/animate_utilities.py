import imageio
import re
import os
import errno


def create_gif(duration_secs, files_to_animate, output_dir, filename_regex):
    '''Logic modified from the sample code found on the website "How To Create GIF Animation with Python"
        http://www.idiotinside.com/2017/06/06/create-gif-animation-with-python

        The original code is for running from the command line and the user does not get to chose the output
        directory and output filename.
        The code example provides a script that reads from the command line the duration (seconds) and
        a whitespace-separated list of png or jpg files to include in the gif.  The output gif is saved in the location
        where the command line input was input, and the resulting file has the format Gif-YYYY-MM-DD-hh-mm-ss

        In this version, the command line support has been removed and the full path to the input png/jpg files is
        required, along with the duration time (in seconds) for each 'frame'.  The output files are located in the
        same output directory specified by the user and the output filename format is a variation of the input filename:
        series_<var>_<level_type><level>_<stat>.gif  The filename_regex is used to extract the var, level_type, level,
        stat from the input file to create the output filename.
    '''

    images = [imageio.imread(filename) for filename in files_to_animate]

    output_file = create_output_filename(output_dir, files_to_animate[0], filename_regex)
    imageio.mimsave(output_file, images, duration=duration_secs)


def create_output_filename(output_dir, file_to_animate, filename_regex):
    ''' Create an output file using the directory specified by the user, and based on one of the input files (minus
         the Fxyz portion, hence only one sampe is needed), '''

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
