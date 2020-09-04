README

**Description**

CBL_plot.py is the plotting only portion of the original CBL.py
script created by Univerity of Illinois/ Doug Miller

These files are used by the image comparison test in test_cbl_plotting.py:

* Z500dayDJF.nc - is the input data that resides on host 'eyewall' under the /d1/blocking_S2S_METplotpy/CBL directory

* CBL_compute.py - calculates the blocking layer and then invokes the method in CBL_plot.py to generate the
                   .pdf and .png


* CBL_DJF_expected.png - is the plot that should be generated when you run CBL_compute.py


**How to use**

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
