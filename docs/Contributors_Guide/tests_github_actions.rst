****************************************
Generate Tests and Add to Github Actions
****************************************

Create a subdirectory under the *test* directory
(e.g. *test/<newplot>* where **<newplot>** is replaced with the
name of the plot type that is being added to the repository.)

Add sample data (see applicable information in the
`Adding a New Plot
<https://metplotpy.readthedocs.io/en/feature_224_contributors_guide/Contributors_Guide/new_plot.html#adding-a-new-plot>`_
section).

Use the pytest framework to generate tests.

Add an entry for the test in the
*.github/workflows/unit_tests.yaml* file.
