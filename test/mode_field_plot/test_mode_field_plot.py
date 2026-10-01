import os
import pytest
from pathlib import Path
import matplotlib.testing.compare
from metplotpy.plots.mode_field_plot  import mode_field_plot
from metplotpy.plots  import util


@pytest.mark.parametrize("input_yaml, generated_files", [
    ("test_mode_field_plot_objects.yaml",
       [ "apcp_example_mode_objects.png"]),
    ("test_mode_field_plot_raw.yaml",
       [ "apcp_example_mode_raw.png"])
    ])
def test_compare_figures(module_setup_env, remove_files, input_yaml, generated_files):
   """
      Verifies that the generated files are created and pass the comparison thresholds
      in matplotlib.testing.compare

   :param module_setup_env:
   :param remove_files:
   :param input_yaml:
   :param generated_files:
   :return:
   """

   metplotpy_base_dir = Path(__file__).parents[2]
   os.environ['METPLOTPY_BASE'] = str(metplotpy_base_dir)
   test_dir = os.getenv('TEST_DIR')
   test_outputdir = os.path.join(os.getenv('TEST_OUTPUT'))

   # Reference plots for MODE object and raw fields
   ref_objects = os.path.join(test_dir, 'expected_apcp_example_mode_objects.png')
   ref_raw = os.path.join(test_dir, 'expected_apcp_example_mode_raw.png')

   curr_yaml = f"{os.getenv('TEST_DIR')}/{input_yaml}"
   params = util.get_params(curr_yaml)
   mfp =  mode_field_plot.ModeFieldPlot(params)

   for cur_file in generated_files:
      plot_file = os.path.join(test_outputdir, cur_file)
      tolerance:int = int(1)
      if mfp.config_obj.field_to_plot == "raw":
          mfp.plot_mode_raw()
          assert os.path.exists(plot_file)

          # 1 pixel tolerance (color value difference, 255 is max value)
          # None is returned when there are no differences for the specified tolerance
          assert Path.is_file(plot_file)
          raw_comp_result = matplotlib.testing.compare.compare_images(ref_raw, plot_file, tolerance,True)
          assert raw_comp_result is None
      else:
          mfp.plot_mode_objects()
          assert Path.is_file(plot_file)
          obj_comp_result = matplotlib.testing.compare.compare_images(ref_objects, plot_file,  tolerance, True)
          assert obj_comp_result is None

