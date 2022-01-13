*********
MJO Plots
*********

Description
===========
The **compute_mjo_indices.py** code (found in the METplotpy repository)
supports the generation of RMM, OMI, and phase diagrams from MJO indices.
These indices are calculated by **compute_mjo_indices.py** in the METcalcpy
repository. These modules are used as part of METplus use cases
on generating these three diagrams.


Run from the Command Line
=========================

There are `METplus use cases
<https://metplus.readthedocs.io/en/latest/generated/model_applications/index.html#subseasonal-to-seasonal>`_
which illustrate how to generate RMM and OMI plots:

* To generate an RMM diagram, follow the instructions under the
  "Make RMM plot from calculated MJO Indices" link.

* To generate an OMI diagram, follow the instructions under the
  "Make OMI plot from calculated MJO Indices" link.

Instructions for obtaining sample data and all necessary configuration files
are indicated in the use cases. The use cases invoke the necessary
modules from the METplotpy and METcalcpy repositories.  


Required Packages:
==================

* metplotpy
* numpy 




