*****************************
METplotpy Release Information
*****************************

When applicable, release notes are followed by the GitHub issue number which
describes the bugfix, enhancement, or new feature:
`METplotpy GitHub issues. <https://github.com/dtcenter/METplotpy/issues>`_


METplotpy Version 13.0.0-beta2 release notes (20260507)
=======================================================

.. dropdown:: New Plots

   None

.. dropdown:: Enhancements

   * **Remove plotly dependency** (`#555 <https://github.com/dtcenter/METplotpy/issues/555>`_)
   * Remove plotly: Create copy of base/common functionality using matplotlib  (`#556 <https://github.com/dtcenter/METplotpy/issues/556>`_)
   * Remove scikit-image package from nco_requirements.txt and requirements.txt  (`#565 <https://github.com/dtcenter/METplotpy/issues/565>`_)
   * Remove plotly: Update bar, box, and histogramm plot (`#558 <https://github.com/dtcenter/METplotpy/issues/558>`_)
   * Remove plotly: Update ROC diagram, Reliability diagram, and ens_ss plots  (`#569 <https://github.com/dtcenter/METplotpy/issues/569>`_)
   * Remove plotly: Update contour plot  (`#572 <https://github.com/dtcenter/METplotpy/issues/572>`_)
   * Remove plotly: Wind Rose, MPR, Hovmoeller, TCMPR, 2D Histogram  (`#574 <https://github.com/dtcenter/METplotpy/pull/574>`_)
   * Remove plotly: Update line, eclv, equivalence testing bounds, and revision series (`#557 <https://github.com/dtcenter/METplotpy/issues/557>`_)

.. dropdown:: Bugfixes


.. dropdown:: Documentation

   * None

.. dropdown:: Repository, build, and test

   * None


METplotpy Version 13.0.0-beta1 release notes (20260205)
=======================================================

.. dropdown:: New Plots

   None

.. dropdown:: Enhancements

   * None

.. dropdown:: Bugfixes

   * Use the METviewer data output directory when the points path is not defined in the yaml config file created by METviewer (`#552 <https://github.com/dtcenter/METplotpy/issues/552>`_)
   * WindRose plot shows incorrect legend when max wind speed is less than requested (`#547 <https://github.com/dtcenter/METplotpy/issues/547>`_)

.. dropdown:: Documentation

   * None

.. dropdown:: Repository, build, and test

   * None


METplotpy Upgrade Instructions
==============================

This section summarizes and highlights important changes to METplotpy since version 3.1.0, including:

.. note::
  
   Plots that originally utilized the Python Plotly plotting package are now using Matplotlib. As a result, all plots in this repository utilize Matplotlib.  This removes the dependency on chrome by the kaleido module in Plotly. The kaleido/chrome dependency required run-time downloading of chrome and also broke existing functionality.   

   The version numbering for METplotpy has been updated to 13.0.0 to provide consistency and clarity with all METplus components.  View the requirements.txt/nco_requirements.txt file at the top level of the repository for version numbers for the corresponding third-party packages.
