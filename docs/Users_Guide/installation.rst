************
Installation
************

Installation guide for METplotpy
================================

METplotpy is written entirely in Python and uses YAML configuration files
and relies on the METcalcpy package. The version numbers (when provided)
indicate the *minimum* version number for that package.  Some plots may require
additional packages that are not listed below.

.. _python_req:

Python Requirements
___________________

* Python 3.10.4 and above

* cartopy 0.21.1 

* eofs 1.4.0

* imutils 0.5.4

* imageio 2.25.0

* matplotlib 3.6.3

* metcalcpy (same version as this version of METplotpy)

* metpy 1.4.0

* netcdf4 1.6.2

* numpy 1.24.2

* opencv-python 4.7.0

* pandas 1.5.2 

* pint 0.20.1

* plotly 5.13.0

* python-kaleido 0.2.1

* pytest 7.2.1

* pyyaml 6.0

* scikit-image 0.19.3

* scikit-learn 1.2.1 

* scipy 1.9.3

* xarray 2023.1.0


.. _METcalcpy_conda:

Install METcalcpy in the conda environment
__________________________________________

This is the recommended method for installation.

Clone the `METcalcpy repository from GitHub
<https://github.com/dtcenter/METcalcpy>`_.

From within the *active* conda environment, change directories
to the METcalcpy directory. This is the directory where the 
METcalcpy repository was cloned. In this directory, 
find the **setup.py** script.

From the command line run:

.. code-block:: ini
		
  pip install -e .

Do NOT forget the ending period **'.'**  This indicates the **setup.py**
is being used in the current working directory.
 
The *-e* option allows this installation to be editable, which is useful if
the *METcalcpy/metcalcpy* source code needs updating. Using the *-e* option
will avoid the need to reinstall if any changes are made to the METcalcpy
code.

Setting up the PYTHONPATH
_________________________

This is a workaround for users who can not or do not have permission to
create conda environments.

*$METCALCPY_SOURCE* is the path downloaded/cloned METcalcpy code. *$METPLOTPY_SOURCE* is the path of the
downloaded/cloned METplotpy code.

**Command for csh:** 

.. code-block:: ini

  setenv PYTHONPATH $METCALCPY_SOURCE/METcalcpy:$METCALCPY_SOURCE/METcalcpy/util:$METPLOTPY_SOURCE/METplotpy${PYTHONPATH}

**Command for bash:**

.. code-block:: ini

  export PYTHONPATH=\
  $METCALCPY_SOURCE/METcalcpy:$METCALCPY_SOURCE/METcalcpy/util:$METPLOTPY_SOURCE/METplotpy${PYTHONPATH}

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
differ from the packages and versions specified in the
:numref:`python_req` section.
