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
code used to create the plot

   b. Sample Data with Tests in METplotpy/test/*plotname* directory

      **Sample data must be under 50 MB**

   c. Sample data that exceeds 50 MB can be added to the METplus tarball

      Refer to Section 8.5.1 in the METplus Contributor's Guide
      for steps to add data to the METplus tarball:

    https://metplus.readthedocs.io/en/develop/Contributors_Guide/add_use_case.html

   d.  Test code in the METplotpy/test/**plotname** directory

        Test code should be created using the pytest framework, utilizing
        sample data that can be readily run.

YAML Configuration file
=======================

Use YAML configuration file(s) to set plot properties,
input data, output filename, etc.


**METviewer Plots**

For plots that are used by METviewer, two YAML configuration files are needed:
a default configuration file and a custom config file.

The default configuration file is used by METviewer.  The custom configuration
file is required.  It can be an empty file if the default settings are to be applied.
The default config file is named with the naming convention
*plotname*_defaults.yaml.  Custom configuration files are saved in the
METplotpy/test/*plotname* directory.  In addition to being used for testing, these
custom configuration files are used in the user documentation to illustrate how to
generate the plot.

**Contributed Plots**

The plots in the METplotpy/metplotpy/contributed have been contributed from
various sources and do not follow a specific pattern.  It is however suggested
that when contributing plots, every effort is made to enable configurability
by way of YAML configuration files and to avoid hard-coding of plot settings,
input file paths, output file paths, etc.







