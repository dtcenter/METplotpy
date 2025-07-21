*****************************
METplotpy Release Information
*****************************

When applicable, release notes are followed by the GitHub issue number which
describes the bugfix, enhancement, or new feature:
`METplotpy GitHub issues. <https://github.com/dtcenter/METplotpy/issues>`_


METplotpy Version 3.1.0 release notes (20250721)
====================================================

.. dropdown:: New Plots

   None

.. dropdown:: Enhancements

  * Enhance the scatter plot to support marginal distributions and generalize the inputs and plotting options (`#23 <https://github.com/dtcenter/METplotpy/issues/23>`_)
  * Remove defunct scatter plot code from METplotpy/plots  (`#458 <https://github.com/dtcenter/METplotpy/issues/458>`_)
  * Optimize plotting in the Physics Tendency planview, cross-section, and vertical cross-section plots (`#449 <https://github.com/dtcenter/METplotpy/issues/449>`_)


.. dropdown:: Bugfixes

   * Make default configs available in package (`#476 <https://github.com/dtcenter/METplotpy/issues/476>`_)
   * Import from metplotpy.contributed instead of relative import (`#478 <https://github.com/dtcenter/METplotpy/issues/478>`_)
   * Series names in legend don't get ordered correctly  (`#347 <https://github.com/dtcenter/METplotpy/issues/347>`_)
   * Support various formats of show_legend values (`#482 <https://github.com/dtcenter/METplotpy/issues/482>`_)
   * Reliability Diagram show_legend setting should work with True/False rather than 1/0 values; see bugfix #482 (`#455 <https://github.com/dtcenter/METplotpy/issues/455>`_)
   * Better handling of determining min and max for confidence limits when data contains NaN values (`#494 <https://github.com/dtcenter/METplotpy/issues/494>`_)
   * Plotly line plots are plotting confidence limit bars at zero with zero length error bars (`#495 <https://github.com/dtcenter/METplotpy/issues/495>`_)



.. dropdown:: Documentation

   * Enhance METplotpy User's Guide Installation Instructions (`#457 <https://github.com/dtcenter/METplotpy/issues/457>`_)
   * Provide more background information on the Taylor Diagram (`#435 <https://github.com/dtcenter/METplotpy/issues/435>`_)
   * Enhance the Table of Contents to include all METplus components (`#499 <https://github.com/dtcenter/METplotpy/pull/499>`_)
   * Documentation: TCMPR filtering (`#507 <https://github.com/dtcenter/METplotpy/issues/507>`_)

.. dropdown:: Repository, build, and test

   * Update infrastructure to reflect move to developing with Python 3.12 (`#496 <https://github.com/dtcenter/METplotpy/pull/496>`_)
   * Update modulefiles used on various machines (`#488 <https://github.com/dtcenter/METplotpy/issues/488>`_)


METplotpy Upgrade Instructions
==============================

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
