Installation guide for METplotpy
===========================================

METplotpy is written entirely in Python and uses YAML configuration files and relies
on the METcalcpy package. The version numbers (when provided) indicate the *minimum* version
number for that package.


Python Requirements
~~~~~~~~~~~~~~~~~~~

* Python 3.6.3

* cartopy 0.18.0

* cmocean

* eofs

* imutils 0.5.3

* imageio 

* lxml

* matplotlib 3.3.0

* metcalcpy 

* netcdf4 1.5.1.2

* numpy 1.17.0

* pandas 1.0.1

* plotly 4.9.0

* python-kaleido 0.2.1

* psutil 5.7.2

* pymysql

* pytest 5.2.1

* pyyaml 5.3.1

* scikit-image 0.16.2

* scikit-learn 0.23.2

* scipy 1.5.1

* statsmodels 0.11.1

* xarray 0.16.2


Install METcalcpy in your conda environment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This is the recommended method for installation.

Clone the METcalcpy repository from https://github.com/dtcenter/METcalcpy

From within your *active* conda environment, cd to the METcalcpy/ directory.  This is the directory
where you cloned the METcalcpy repository. In this directory, you should see a setup.py script

From the command line, run *pip install -e .*

Do NOT forget the ending **'.'**  this indicates that you should use the setup.py in the current working directory.
 
The *-e* option allows this installation to be editable, which is useful if you plan on updating your METcalcpy/metcalcpy
source code.  This allows you to avoid reinstalling if you make any changes to your METcalcpy code.

Setting up your PYTHONPATH
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This is a workaround for users who can not or do not have permission to create conda environments.

$METCALCPY_SOURCE is the path to where you downloaded/cloned the METcalcpy code.

**command for csh:** 

setenv PYTHONPATH $METCALCPY_SOURCE/METcalcpy:$METCALCPY_SOURCE/METcalcpy/util:${PYTHONPATH}

**command for bash:**

export PYTHONPATH=\

$METCALCPY_SOURCE/METcalcpy:$METCALCPY_SOURCE/METcalcpy/util:${PYTHONPATH}

Overview of Plots
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The plots in the METplotpy repository reside under one of two directories: *METplotpy/metplotpy/contributed* and
*METplotpy/metplotpy/plots*.

The plots under the *METplotpy/metplotpy/contributed* directory correspond to plots that were either created prior
to the creation of the METplotpy repository, and/or developed outside of the DTC.  The plots that reside in the
*METplotpy/metplotpy/plots* directory were developed by the DTC and were primarily created to replace the R script
implementation of plotting done in METviewer.  These plots were written using Python plotly,  with the exception of
the performance diagram, which was written using Matplotlib.  The plots in the contributed directory may have different
Python and third party Python package requirements that differ from the packages and versions
specified in the 'Python Requirements' section.










