**These files are used by the image comparison test in test_cbl_plotting.py**

**Z500dayDJF.nc**
     is the input data, which is ~871 MB file and exceeds GitHub's 100 MB file size limit.
     Get this file from host 'eyewall' under the directory:
     */d1/blocking_S2S_METplotpy/CBL*

**CBL_compute.py**
     calculates the blocking layer and then invokes the method in CBL_plot.py to generate the
     .pdf and .png

**CBL_DJF_expected.png**
     is the plot that should be generated when you run CBL_compute.py
