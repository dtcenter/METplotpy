************
INSTALLATION
************

Installation guide for METplotpy
================================

METplotpy is written entirely in Python and uses YAML configuration files
and relies on the METcalcpy package. The version numbers (when provided)
indicate the *minimum* version number for that package.


Python Requirements
___________________

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


Install METcalcpy in the conda environment
__________________________________________

This is the recommended method for installation.

Clone the METcalcpy repository from https://github.com/dtcenter/METcalcpy

From within the *active* conda environment:

.. code-block:: ini
		
  cd to the METcalcpy/ directory.

This is the directory where the METcalcpy repository was cloned. In
this directory, find the setup.py script

From the command line run:

.. code-block:: ini
		
  pip install -e .

Do NOT forget the ending period **'.'**  This indicates using the setup.py
in the current working directory.
 
The *-e* option allows this installation to be editable, which is useful if
the METcalcpy/metcalcpy source code needs updating. Using the *-e* option
will avoid the need to reinstall if any changes are made to the METcalcpy
code.

Setting up the PYTHONPATH
_________________________

This is a workaround for users who can not or do not have permission to
create conda environments.

$METCALCPY_SOURCE is the path downloaded/cloned METcalcpy code.

**command for csh:** 

.. code-block:: ini

  setenv PYTHONPATH $METCALCPY_SOURCE/METcalcpy:$METCALCPY_SOURCE/METcalcpy/util:${PYTHONPATH}

**command for bash:**

.. code-block:: ini

  export PYTHONPATH=\
  $METCALCPY_SOURCE/METcalcpy:$METCALCPY_SOURCE/METcalcpy/util:${PYTHONPATH}

Overview of Plots
_________________

The plots in the METplotpy repository reside under one of two directories:
*METplotpy/metplotpy/contributed* or
*METplotpy/metplotpy/plots*.

The plots under the *METplotpy/metplotpy/contributed* directory correspond
to plots that were either created prior to the creation of the METplotpy
repository, and/or developed outside of the DTC.

The plots that reside in the *METplotpy/metplotpy/plots* directory were
developed by the DTC and were primarily created to replace the R script
implementation of plotting done in METviewer.  These plots were written
using Python plotly, with the exception of the performance diagram, which
was written using Matplotlib.  The plots in the contributed directory may
have different Python and third party Python package requirements that
differ from the packages and versions specified in the 'Python Requirements'
section.
