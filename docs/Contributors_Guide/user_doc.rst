*********************
Add User Documenation
*********************

Documentation should be added in the *docs/Users_Guide* directory.

1.
Create a new **.rst** file for the new plot type.

  Put the documentation in a file called **<plot.rst>**,
  where **<plot>** is replaced with the name of the new plot type.

2.
Add the name of the new file to the Table of Contents.

  In the *docs/Users_Guide/index.rst* file, scroll to the bottom of the page,
  and add **<plot>** (without the .rst extension) to an appropriate place
  in the list of files below “toctree”, which becomes the table of
  contents after rendering. Please pay attention to grouping or
  alphabetizing that is already in use.

3.
Add images.

  Add and commit any new images of plots in the *docs/Users_Guide* directory.


4.
Review and check for errors in the automatically generated documentation.

  Once the documentation has been committed and pushed to GitHub,
  GitHub actions will automatically create the online documentation. 

  Contributors will be able to view the run for the build of the documentation
  in the GitHub actions section of the METplotpy repository, which will
  be named with the text of the last commit message and the
  text “Documentation” underneath.  

    a.
    If there is a yellow circle, the build is not yet finished.

    b.
    If there is a green check, the task completed successfully. 

    c.
    If there is a red “x”, the task did not build correctly.
    Find the **documentation_warnings.log** file by clicking on the name of
    the task that failed and scrolling down to the “Archives” section.
    Click on the “**documentation_warnings.log**” file to download it
    and look at the warnings or errors given with the line number and page.
    Resolve any warnings or errors.

  Once the documentation has been successfully built, it will be viewable at this URL:

    .. code-block:: ini

       https://metplotpy.readthedocs.io/en/<feature_branch_name>/Users_Guide/index.html

  where **<feature_branch_name>** is replaced with the name of the
  feature branch.
