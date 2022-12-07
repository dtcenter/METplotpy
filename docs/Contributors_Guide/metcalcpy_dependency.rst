********************
METcalcpy Dependency
********************

Numerous METplotpy plots use METcalcpy packages. Users will need to:

1.
Perform a git clone of the METcalcpy repository and use the develop branch.
   
  .. code-block:: ini
     
    git clone https://github.com/dtcenter/METcalcpy
    git checkout develop

2.
Set the PYTHONPATH to point to the location of the METcalcpy
code (from the command line):

  .. code-block:: ini

    bash:  export PYTHONPATH=/path/to/METcalcpy:/path/to/METcalcpy/metcalcpy
    csh: setenv PYTHONPATH /path/to/METcalcpy:/path/to/METcalcpy/metcalcpy

