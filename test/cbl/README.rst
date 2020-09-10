**!!!!BEFORE RUNNING TESTS!!!**

**Activate conda environment in subshell**


Change the top line:

*#! /usr/bin/env conda run -n blenny_363 python*

in test_cbl_plotting.py to

*#! /usr/bin/env conda run -n your-conda-env python*

Where *your-conda-env* is the python 3.6.3 conda environment
that contains all the python packages required to run
METplotpy and METcalcpy (i.e. replace the *blenny_363*
above with your conda env name)


**GET the netCDF input file**

on host 'eyewall', under the directory:

    **/d1/blocking_S2S_METplotpy/CBL**

    get the file:

    **Z500dayDJF.nc**

    and save it under the METplotpy/metplotpy/blocking_s2s directory
