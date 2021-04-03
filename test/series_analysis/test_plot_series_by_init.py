"""Tests for the plot_series_by_init.py script, on the TMP variable using
   the sample data on the host 'eyewall': /d1/METplus_Plotting_Data/series_by_init
"""
import os, shutil, sys
import yaml
import warnings
import matplotlib
sys.path.append("../../metplotpy")
from contributed.series_analysis.plot_series_by_init import PlotSeriesByInit

# ignore the MatplotlibFutureDeprecation warning which does not affect this code
# since changes must be made to Cartopy
warnings.simplefilter(action='ignore', category=matplotlib.cbook.mplDeprecation)


def test_expected_files_created():
    """
        Testing that the expected png files for OBAR and FBAR are created in
        the expected directory:
        ../expected_output/TMP_Z2_fbar.png
        ../expected_output/TMP_Z2_obar.png

    :param
    :return:
    """

    # Generate the FBAR and OBAR plots for the TMP at level Z2
    config_file = "./series_init.yaml"

    with open(config_file, 'r') as stream:
        try:
            config = yaml.load(stream, Loader=yaml.FullLoader)
        except yaml.YAMLError as exc:
            print(exc)

    # Invoke the function that generates the plot
    psbi = PlotSeriesByInit(config)
    psbi.create_plot()




    # Get all the files that are in the
    # /d1/project/METplus/METplus_Plotting_Output/
    # directory and verify that the plots we are expecting are found in that directory.

    output_dir = psbi.config['output_dir']
    all_files = []
    for root, dirs, files in os.walk(output_dir):
        for cur_file in files:
            if cur_file.endswith('png'):
               all_files.append(cur_file)


    expected_files = ['TMP_Z2_fbar.png',
                      'TMP_Z2_obar.png']

    for expected in expected_files:
        assert (expected in all_files)
        curfile = os.path.join(output_dir, expected)
        # print( "file size of ", curfile, " is: ", os.path.getsize(curfile))
        assert( os.path.getsize(curfile) > 0)


if __name__ == "__main__":
    test_expected_files_created()