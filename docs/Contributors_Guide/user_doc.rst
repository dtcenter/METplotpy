*********************
Add User Documenation
*********************

Documentation should be added in the *docs/Users_Guide* directory.

1.
Create a new **.rst** file for the new plot type.

Put the documentation in a file called **plot.rst**,
where **plot** is replaced with the name of the new plot type.

2.
Add the new section to the Table of Contents.

In the *docs/Users_Guide/index.rst* file, scroll to the bottom of the page,
and add **plot** (without the .rst extension) to an appropriate place
in the list of files below “toctree”, which becomes the table of
contents after rendering. Please pay attention to grouping or
alphabetizing that is already in use.

3.
Add images

Add and commit any new images of plots in the *docs/Users_Guide* directory.

4.
Verify a Clean Build


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


5.
Look for any warnings or error messages in the stdout.

6.
View the documentation for correctness by opening up the browser and entering:

   .. code-block:: ini

      file:///<path-to-your-source-code>/METplotpy/docs/_build/html/Users_Guide/index.html

7.
Verify that the plot is in the table of contents on the left bar of the
documentation.

8.
Verify that the documentation looks correct and any images are rendered correctly.


