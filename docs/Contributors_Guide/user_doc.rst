*********************
Add User Documenation
*********************

This will be added in the METplotpy/docs/Users_Guide


New Plot File Name
==================

Put user documentation in a file called <plot>.rst,
where <plot> is the name of the new plot.

Add New Name to the Table of Contents
=====================================

In the `index.rst file <https://metplotpy.readthedocs.io/en/latest/Users_Guide/index.html>`_,
add <plot> (without the .rst extension) to the table of contents.
To do this, add <plot> to the list below the toctree:: entry.
Please pay attention to grouping or alphabetizing that is already in use.

Verify a Clean Build
====================

Installation Items
------------------

The below items must be installed on the local system or in the virtual environment
(virtualenv or conda) for this to run.

  * sphinx
  * sphinx-rtd-themes
  * sphinx-gallery

From the METplotpy/docs directory, run the following:  

.. code-block:: ini
		
  make clean  
  make html


Look for any warnings or error messages in the stdout
view the documentation for correctness by opening up the browser and entering:
file:///<path-to-your-source-code>/METplotpy/docs/_build/html/Users_Guide/index.html
Verify that the plot is in the table of contents on the left bar of the documentation.
Click on the plot and verify that the documentation is correct and any images
are rendered correctly.


