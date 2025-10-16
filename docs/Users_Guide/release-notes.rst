*****************************
METplotpy Release Information
*****************************

When applicable, release notes are followed by the GitHub issue number which
describes the bugfix, enhancement, or new feature:
`METplotpy GitHub issues. <https://github.com/dtcenter/METplotpy/issues>`_


METplotpy Release Notes
=======================


METplotpy Version 3.0.2 release notes (20251016)
------------------------------------------------

  .. dropdown:: New Plots

     None


  .. dropdown:: Enhancements
 

     None


  .. dropdown:: Internal

     None



  .. dropdown:: Bugfixes

     * Check for incorrectly formatted fixed_vars_vals_input value that is created by METviewer's MVBatch.java (`007d385 <https://github.com/dtcenter/METplotpy/commit/007d385c496ecc5dc14ff9af22977e1d843d647a>`_).

METplotpy Version 3.0.1 release notes (20250722)
------------------------------------------------------

  .. dropdown:: New Plots

     None


  .. dropdown:: Enhancements
 

     None


  .. dropdown:: Internal

     None



  .. dropdown:: Bugfixes

     * **Incorporate Plotly/kaleido fixes to the main_3.0 code** (`#530 <https://github.com/dtcenter/METplotpy/issues/530>`_).


METplotpy Upgrade Instructions
==============================

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


