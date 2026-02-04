*****************************
METplotpy Release Information
*****************************

When applicable, release notes are followed by the GitHub issue number which
describes the bugfix, enhancement, or new feature:
`METplotpy GitHub issues. <https://github.com/dtcenter/METplotpy/issues>`_


METplotpy Version 4.0.0-beta1 release notes (20260205)
===========================================

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

  In the METplotpy-3.1.0-beta2 release, METplotpy switched from development with Python 3.10.4 to
  development with Python 3.12. View the requirements.txt/nco_requirements.txt file at the top
  level of the repository for version numbers for the corresponding third-party packages.

.. note::

  In June 2025, Plotly made significant updates to the kaleido package with the 1.0.0
  release by removing Google Chrome code.  Now, users will need to have Google Chrome
  installed in directories specified in this Plotly documentation (based on operating
  system):
  https://plotly.com/python/static-image-export/

The METplotpy code downloads Chrome at runtime by invoking the kaleido.get_chrome_sync()
method call.

If users do not wish to have Chrome downloaded at run time and already have Chrome installed
in one of the expected locations (specified in the Plotly link above), then the PRE_LOAD_CHROME environment variable
will need to be set to 'True' (case insensitive string).

Refer to the Kaleido  README for more information on the changes:
https://github.com/plotly/Kaleido
