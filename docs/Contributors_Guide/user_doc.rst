*********************
Add User Documenation
*********************

This will be added in the METplotpy/docs/Users_Guide


1. New Plot File Name

   Put user documentation in a file called <plot>.rst,
   where <plot> is the name of the new plot.

2. Add New Name to the Table of Contents

  In the
  `index.rst file <https://metplotpy.readthedocs.io/en/latest/Users_Guide/index.html>`_,
  add <plot> (without the .rst extension) to the table of contents.
  To do this, add <plot> to the list below the toctree:: entry.
  Please pay attention to grouping or alphabetizing that is already in use.

3. Include Images

   Include any images of plots in the METplotpy/docs/Users_Guide directory

4. Verify a Clean Build


   a. Installation Items

      The below items must be installed on the local system or in the
      virtual environment (virtualenv or conda) for this to run.

      * sphinx
      * sphinx-rtd-themes
      * sphinx-gallery

      From the METplotpy/docs directory, run the following:  

      .. code-block:: ini

	make clean  
	make html


5. Look for any warnings or error messages in the stdout

6. View the documentation for correctness by opening up the browser and entering:

   .. code-block:: ini

      file:///<path-to-your-source-code>/METplotpy/docs/_build/html/Users_Guide/index.html

7. Verify that the plot is in the table of contents on the left bar of the
   documentation.

8. Click on the plot and verify that the documentation is correct and any images
   are rendered correctly.


