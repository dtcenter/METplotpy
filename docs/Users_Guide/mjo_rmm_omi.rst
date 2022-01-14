*********
MJO Plots
*********

Description
===========
The **compute_mjo_indices.py** code (found in the METplotpy repository)
supports the generation of RMM (Real-time Multivariate MJO), OMI (OLR based MJO Index), and phase diagrams from MJO
(Madden-Julien Oscillation) indices.
These indices are calculated by **compute_mjo_indices.py** in the METcalcpy
repository. These modules are used as part of METplus use cases
on generating these three diagrams.


Run from the Command Line
=========================

There are `METplus use cases
<https://metplus.readthedocs.io/en/latest/generated/model_applications/index.html#subseasonal-to-seasonal>`_
which illustrate how to generate RMM and OMI plots:

* To generate an RMM diagram, follow the instructions under the
  `Make a Phase Diagram plot from input RMM or OMI link
  <https://metplus.readthedocs.io/en/develop/generated/model_applications/s2s/UserScript_obsERA_obsOnly_PhaseDiagram.html#sphx-glr-generated-model-applications-s2s-userscript-obsera-obsonly-phasediagram-py>`_.

* To generate an OMI diagram, follow the instructions under the
  `Make OMI plot from calculated MJO Indices link
  <https://metplus.readthedocs.io/en/develop/generated/model_applications/s2s/UserScript_obsERA_obsOnly_OMI.html#sphx-glr-generated-model-applications-s2s-userscript-obsera-obsonly-omi-py>`_.

Instructions for obtaining sample data and all necessary configuration files
are indicated in the use cases. The use cases invoke the necessary
modules from the METplotpy and METcalcpy repositories.  


Required Packages:
==================

* metplotpy
* numpy 




