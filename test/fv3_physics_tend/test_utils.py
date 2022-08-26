import os

'''
utility functions useful for performing tasks needed for testing
the FV3 Physics tendency plots.

'''

def get_fv3_shapefiles_dir(debug=False):
   '''

   :param debug: default is False, prints out directory paths
   :return:  the absolute path to the MID_CONUS shapefiles used in the FV3 physics tendency plots
   '''


   # get the full path of the script is being invoked
   absolute_path = os.path.abspath(__file__)

   # Get just the path to the script
   fv3_test_dir = os.path.dirname(absolute_path)

   # Get the parent directory to the path where the script resides- i.e. the test directory
   test_dir = os.path.dirname(fv3_test_dir)

   # Get the path of the parent to the test directory (i.e. METplotpy/)
   metplotpy_base_dir = os.path.dirname(test_dir)

   # Define the directory where the shapefiles are located
   mid_conus_shapefiles_dir = os.path.join(metplotpy_base_dir, 'metplotpy/contributed/fv3_physics_tend/shapefiles/MID_CONUS')

   if debug:
      print("absolute path: ", absolute_path)
      print("test dir: ", test_dir)
      print("metplotpy base dir: ", metplotpy_base_dir)
      print("shapefiles dir: ", mid_conus_shapefiles_dir)

   return mid_conus_shapefiles_dir


if __name__ == "__main__":
    get_fv3_shapefiles_dir()