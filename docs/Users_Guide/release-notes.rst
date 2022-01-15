*********************************
METplotpy |version| Release Notes
*********************************

When applicable, release notes are followed by the GitHub issue number which
describes the bugfix, enhancement, or new feature: `METplotpy GitHub issues. <https://github.com/dtcenter/METplotpy/issues>`_

Version |version| release notes (|release_date|)
________________________________________________

Version 1.1.0 release notes (20220114)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

beta5 release
^^^^^^^^^^^^^

* New Plots:
   * **Vertical interpolation of fields between pressure and height coordinates (`_#37 <https://github.com/dtcenter/METplotpy/issues/37>`_)
   * **Add the Python implementation of the ECLV plot type (`_#171 <https://github.com/dtcenter/METplotpy/issues/171> `_)
   * **Add supporting functionality for ECLV plot (`_#128 <https://github.com/dtcenter/METcalcpy/issues/128> `_)
   
* Enhancements: 
   * **Enhance hovmoeller.py to log more error messages in failure mode (`_#182 <https://github.com/dtcenter/METplotpy/issues/182>`_)

* Internal:
   * **Modify formatting of METplotpy documentation to make it consistent with other METplus components (`_#155 <https://github.com/dtcenter/METplotpy/issues/155>`_)

* Bugfixes:


beta4 release
^^^^^^^^^^^^^

* New Plots:
   * **Create histogram plots to be used by METviewer** (`#141 <https://github.com/dtcenter/METplotpy/issues/141>`_)

* Enhancements: 
   * **Change the names of the CI data columns from bcl/bcu to btcl/btcu** (`#156 <https://github.com/dtcenter/METplotpy/issues/156>`_)
   * **Write any intermediary files to a user-specified directory** (`#153 <https://github.com/dtcenter/METplotpy/issues/153>`_)

* Internal:


* Bugfixes:
   * **Revision series for MODE-TD** (`#157 <https://github.com/dtcenter/METplotpy/issues/157>`_)

   * **Plots with groups with date values don't get created** (`#163 <https://github.com/dtcenter/METplotpy/issues/163>`_)

   * **Incorrect rendering of plot_val indy values** (`#161 <https://github.com/dtcenter/METplotpy/issues/161>`_)

beta3 release
_____________

* New Plots:

* Enhancements:
  
   * **Remove unused parameter 'list_static_val'**
     (`#150 <https://github.com/dtcenter/METplotpy/issues/150>`_).
   * **Change ',' as a separator for the series group to ':'**
     (`#152 <https://github.com/dtcenter/METplotpy/issues/152>`_).

* Internal:


* Bugfixes:


beta2 release
_____________

* New Plots:
  
   * **Add the weather regime frequency plot to the weather regime code**
     (`#135 <https://github.com/dtcenter/METplotpy/issues/135>`_).
   * **Create bar plot to be used by METviewer**
     (`#126 <https://github.com/dtcenter/METplotpy/issues/126>`_).

* Enhancements:
  
   * **Add support for plotting new G and GBETA statistics**
     (`#142 <https://github.com/dtcenter/METplotpy/issues/142>`_).
   * **Create ens_ss plot to be used by METviewer**
     (`#137 <https://github.com/dtcenter/METplotpy/issues/137>`_).

* Internal:

* Bugfixes:
  
   * **Line plot doesn't work if data column doesn't include "fcst_lead"**
     (`#129 <https://github.com/dtcenter/METplotpy/issues/129>`_).
  

beta1 release
_____________

* New Plots:
  
   * **Create Box plot for METviewer**
     (`#119 <https://github.com/dtcenter/METplotpy/issues/119>`_).
   * **Recreate the functionality of plot_mpr.R**
     (`#9 <https://github.com/dtcenter/METplotpy/issues/9>`_).
   * **Add plotting for the MJO indices: RMM and OMI**
     (`#109 <https://github.com/dtcenter/METplotpy/issues/109>`_).

* Enhancements:
  
   * **Use METcalcpy correlation instead of pingouin library**
     (`#127 <https://github.com/dtcenter/METplotpy/issues/127>`_).

* Internal:

* Bugfixes:
  
   * **Reliability plot- change the names of the CI data columns
     from bcl/bcu to btcl/btcu**
     (`#124 <https://github.com/dtcenter/METplotpy/issues/124>`_).

