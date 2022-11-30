*****************
S2S Blocking plot
*****************

Description
===========


The **CBL_plot.py** is plotting only a portion of the original **CBL.py**
script created by Doug Miller at the University of Illinois.

For more background on this plot, please refer to the `METplus use case
documentation <https://metplus.readthedocs.io/en/develop/generated/model_applications/s2s/UserScript_fcstGFS_obsERA_Blocking.html#sphx-glr-generated-model-applications-s2s-userscript-fcstgfs-obsera-blocking-py>`_.


Required Packages
=================

* Python 3.8

* Matplotlib 3.3.1

* Cartopy 0.17.1

* metcalcpy  (refer to :numref:`METcalcpy_conda`)
  
* numpy

* psutil

* pytest

* pyyaml

* scikit-image

* scipy



How to Use
==========

Import CBL_plot into the script:

.. code-block:: ini
   
   import CBL_plot as cblp

Generate the following as numpy arrays in the code
(except month_str and output_plotname):

* **lons**:  A numpy array of the longitude values under consideration.

* **lats**:  A numpy array of the latitude values under consideration.

* **mmstd**:  A numpy array of the mean weight heights.

* **mean_cbl**:  A numpy array of the mean CBL values that correspond
  to the lons.

* **month_str**:  Indicates the months comprising this plot.
  (ex. DJF for December, January, February.)

* **output_plotname**:  The full path and filename of the output plot file.
  Two versions are written, **.pdf** and **.png** files.


Invoke the plotting function

.. code-block:: ini

  cblp.create_cbl_plot (lons, lats, mean_cbl, mmstd, month_str, output_plotname)


A **.pdf** and **.png** version of the CBL contour world map plot are
generated as output, based on what was specified (path and name) in the
**output_plotname**.

