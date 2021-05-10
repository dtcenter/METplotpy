S2S Blocking plot
===========================================

Description
~~~~~~~~~~~


The CBL_plot.py is the plotting only portion of the original CBL.py
script created by Doug Miller at the Univerity of Illinois.

For more background on this plot, please refer to the METplus use case documentation:

https://metplus.readthedocs.io/en/develop/generated/model_applications/s2s/UserScript_fcstGFS_obsERA_Blocking.html#sphx-glr-generated-model-applications-s2s-userscript-fcstgfs-obsera-blocking-py


Required Packages
~~~~~~~~~~~~~~~~~

* Python 3.6.3

* Matplotlib 3.3.1

* Cartopy 0.17.1

* metcalcpy  (refer to Section 1.2: https://metplotpy.readthedocs.io/en/latest/Users_Guide/installation.html)

* numpy

* psutil

* pytest

* pyyaml

* scikit-image

* scipy




How to Use
~~~~~~~~~~~


Import CBL_plot in your script like so:

*import CBL_plot as cblp*

In your code, generate the following as numpy arrays
(except month_str and output_plotname):

* **lons**:
    a numpy array of the longitude values under consideration

* **lats**:
    a numpy array of the latitude values under consideration

* **mmstd**:
    a numpy array of the mean weight heights

* **mean_cbl**:
    a numpy array of the mean CBL values that correspond to the lons

* **month_str**:
    indicates the months comprising this plot
    (eg. DJF for December January February)

* **output_plotname**:
    The full path and filename of the output plot file
    Two versions are written, .pdf and .png files


**Invoke the plotting function**
    cblp.create_cbl_plot(lons, lats, mean_cbl, mmstd, month_str, output_plotname)


**Output**
    A .pdf and .png version of your CBL contour world
    map plot are generated, based on what you specified
    (path and name) in the **output_plotname**.

