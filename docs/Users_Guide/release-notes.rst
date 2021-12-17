METplotpy |version| Release Notes
_________________________________

When applicable, release notes are followed by the GitHub issue number which
describes the bugfix, enhancement, or new feature: `METplotpy GitHub issues. <https://github.com/dtcenter/METplotpy/issues>`_

Version |version| release notes (|release_date|)
------------------------------------------------

Version 1.0.0 release notes (20210511)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

* New Plots:

   * **Plot the TDF/GDF metrics from METplus use cases (https://github.com/dtcenter/METplus/issues/630,https://github.com/dtcenter/METplus/issues/631)** (`#48 <https://github.com/dtcenter/METplotpy/issues/48>`_)

   * **Add plots for Weather Regime Analysis** (`#74 <https://github.com/dtcenter/METplotpy/issue/74>`_)

   * **Add plots for Coherence Spectra** (`#46 <https://github.com/dtcenter/METplotpy/issue/46>`_)

   * **Replicate METviewer ROC diagram**  (`#11 <https://github.com/dtcenter/METplotpy/issue/11>`_)

   * **Add plots for GridDiag analysis**  (`#36 <https://github.com/dtcenter/METplotpy/issues/36>`_)

   * **Implement Equivalence Testing Bounds plot in Plotly** (`#71 <https://github.com/dtcenter/METplotpy/issues/71>`_)

   * **Recreate plot generated in the blocking Subseasonal to seasonal (S2S) script provided by University of Illinois** (`#40 <https://github.com/dtcenter/METplotpy/issues/40>`_)

   * **Replicate METviewer Reliability diagram using Python** (`_#12 <https://github.com/dtcenter/METplotpy/issues/12>`_)

   * **Plot for Hovmoller Diagram from NOAA PSL Diagnostics package** (`_#45 <https://github.com/dtcenter/METplotpy/issues/45>`_)

   * **Replicate METviewer Performance diagram using Python** (`_#20 <https://github.com/dtcenter/METplotpy/issues/20>`_)

   * Refactor CBL code to isolate plotting and replace Basemap with Cartopy  (`#33 <https://github.com/dtcenter/METplotpy/issues/33>`_)
 
   * **Create line plot** (`#19 <https://github.com/dtcenter/METplotpy/issues/19>`_)
  
   * **Add Difficulty Index plotting from NRL** (`#47 <https://github.com/dtcenter/METplotpy/issues/47>`_)


* Enhancements:

  * Documentation for METviewer plots in the User's Guide: 

	* Line Plot

        * Performance Diagram

        * Reliability Diagram

        * ROC Diagram

  * Documentation for Contributed plots in the User's Guide:

        * Histogram_2d Plot

        * S2S Blocking 

        * Weather Regime

        * Hovmoeller Plot

        * Spacetime (cross-spectra) Plot


   * Restructure the Conf Interval dropdown list (`#99 <https://github.com/dtcenter/METplotpy/issues/99>`_)

   * Add support to reverse the connection order for ROC (`#81 <https://github.com/dtcenter/METplotpy/issues/81>`_)

   * Series plot support for "group" statistics (`#88 <https://github.com/dtcenter/METplotpy/issues/88>`_)

   * Add a version selector for documentation (`#60 <https://github.com/dtcenter/METplotpy/issues/60>`_)

   * Include more Python packages to the conda environment (`_#52 <https://github.com/dtcenter/METplotpy/issues/52>`_)


* Internal:

   * Move the documentation over to Read The Docs (`#73 <https://github.com/dtcenter/METplotpy/issues/84>`_)

   * Make sure all tests are working (`#73 <https://github.com/dtcenter/METplotpy/issues/73>`_)

   * Setup METplotpy docs to use github actions (`#100 <https://github.com/dtcenter/METplotpy/issues/100>`_)

   * Rename the met_plot.py and MetPlot class name (`#69 <https://github.com/dtcenter/METplotpy/issues/69>`_)
 
   * Automate release date for automation (`#62 <https://github.com/dtcenter/METplotpy/issues/62>`_)

   * Version selector for sphinx documentation (`_#63 <https://github.com/dtcenter/METplotpy/issues/63>`_)

   * Use new METcalcpy permutation calculation for the line plot (`_#61 <https://github.com/dtcenter/METplotpy/issues/61>`_)

 
* Bugfixes:
    
    * Difficulty index plot loses data at edges (`#76 <https://github.com/dtcenter/METplotpy/issues/76>`_)

