*****************************
METplotpy Release Information
*****************************

When applicable, release notes are followed by the GitHub issue number which
describes the bugfix, enhancement, or new feature:
`METplotpy GitHub issues. <https://github.com/dtcenter/METplotpy/issues>`_


METplotpy Release Notes
=======================

METplotpy Version 2.0.0-beta5 release notes (20221115)
------------------------------------------------------

* New Plots:


* Enhancements: 



* Internal:



* Bugfixes:




METplotpy Version 2.0.0-beta4 release notes (20221028)
------------------------------------------------------

* New Plots:


* Enhancements: 

   * **Remove statsmodels and patsy python packages**
     (`#275 <https://github.com/dtcenter/METplotpy/issues/275>`_).


* Internal:

   * **Clean up release notes**
     (`#273 <https://github.com/dtcenter/METplotpy/issues/273>`_).

   * **Fix github Actions warnings**
     (`#272 <https://github.com/dtcenter/METplotpy/issues/272>`_).


* Bugfixes:

   * **Fix ensemble spread-skill plot to correctly read in ensemble spread-skill file**
     (`#271 <https://github.com/dtcenter/METplotpy/issues/271>`_).

   * **Fix type cast issue caused by Python 3.8**
     (`#269 <https://github.com/dtcenter/METplotpy/issues/269>`_).

   * **Fix import statements in revision_series plot**
     (`#267 <https://github.com/dtcenter/METplotpy/issues/267>`_).



METplotpy Version 2.0.0-beta3 release notes (20220914)
------------------------------------------------------

* New Plots:

   * **Analyze FV3 Physics Parameterization Tendencies**
     (`#117 <https://github.com/dtcenter/METplotpy/issues/117>`_).


* Enhancements: 


* Internal:

   * **Create checksum for released code**
     (`#262 <https://github.com/dtcenter/METplotpy/issues/262>`_).


   * Add modulefiles used for installations on various machines
     (`#251 <https://github.com/dtcenter/METplotpy/issues/251>`_).

* Bugfixes:




METplotpy Version 2.0.0-beta2 release notes (20220803)
------------------------------------------------------


* New Plots:

* Enhancements: 

   * **Add Revision Series Capability to line and box plots**
     (`#232 <https://github.com/dtcenter/METplotpy/issues/232>`_).
   
   * **Set up SonarQube to run nightly**
     (`#38 <https://github.com/dtcenter/METplus-Internal/issues/38>`_).


* Internal:


* Bugfixes:

   * **Fix logic to guess path to default config when
     METPLOTPY_BASE is not set**
     (`#238 <https://github.com/dtcenter/METplotpy/issues/238>`_).


METplotpy Version 2.0.0-beta1 release notes (20220622)
------------------------------------------------------


* New Plots:


* Enhancements: 

   * **Allow line plots to start from y=0 line**
     (`#217 <https://github.com/dtcenter/METplotpy/issues/217>`_).
   * **Make hovmoeller plot more configurable**
     (`#213 <https://github.com/dtcenter/METplotpy/issues/213>`_).

* Internal:

  * Identify minimal, "bare-bones" Python packages for NCO operational HPC
    (`#208 <https://github.com/dtcenter/METplotpy/issues/208>`_).


* Bugfixes:

  * Fix/handle deprecation, future, and runtime warnings in
    line plot, ensemble spread-skill, mpr plot, reliability plot
    (`#230 <https://github.com/dtcenter/METplotpy/issues/230>`_).
  * Add default operation value "DIFF" to the derived series
    (`#226 <https://github.com/dtcenter/METplotpy/issues/226>`_).
  * Issues with generating points1 files for numerous plots
    (`#223 <https://github.com/dtcenter/METplotpy/issues/223>`_).

METplotpy Upgrade Instructions
==============================

Upgrade instructions will be listed here if they are
applicable for this release.
