*****************
Adding a New Plot
*****************

1.
Generate a GitHub issue.

2.
Create a feature branch in the GitHub repository.

3.
Place all code in the appropriate locations:

  a.
  *metplotpy/plots* vs *metplotpy/contributed* for source
  code used to create the plot.

  b.
  Sample data for testing should be placed in *test/<plotname>* directory,
  where **<plotname>** is replaced with the name of the plot (e.g. bar, box,
  etc.). The size of the sample data must be **under 50 MB.**

  c.
  If the sample data size exceeds 50 MB it should be added to the METplus tar files.
  Refer to the `Providing New Data
  <https://metplus.readthedocs.io/en/latest/Contributors_Guide/add_use_case.html>`_
  section of the METplus Contributor's Guide for steps to add data.

  d.
  Test code should be placed in the *test/<plotname>* directory,
  where **<plotname>** is replaced with the name of the plot (e.g. bar, box,
  etc.). The test code should be created using the pytest framework,
  utilizing sample data that can be readily run.

YAML Configuration file
=======================

Use YAML configuration file(s) to set plot properties, input data, output
filename, etc.


METviewer Plots
---------------

For plots that are used by METviewer, two YAML configuration files are needed:
a default configuration file and a custom config file.

The default configuration files are used by METviewer and are located in
*metplotpy/plots/config*. The default config file should be named using the
naming convention **<plotname>_defaults.yaml**, where **<plotname>** is replaced
with the name of the plot (e.g. bar, box, etc.).

The custom configuration file is required. It can be an empty file if the
default settings are to be applied. Custom configuration files are located
in the *test/<plotname>* directory, where **<plotname>** is replaced with the name
of the plot (e.g. box, bar, etc.).  In addition to being used for testing,
these custom configuration files are used in the user documentation to
illustrate how to generate the plot.


Contributed Plots
-----------------

The plots in *metplotpy/contributed* have been contributed from
various sources and do not follow a specific pattern.  However, it is
recommended that when contributing plots, every effort is made to enable
configurability by way of YAML configuration files and to avoid
hard-coding of plot settings, input file paths, output file paths, etc.






