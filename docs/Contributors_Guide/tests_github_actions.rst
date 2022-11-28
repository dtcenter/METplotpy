****************************************
Generate Tests and Add to Github Actions
****************************************

Create a directory under the
METplotpy/test directory/*newplot*;
replace *newplot* with the name of the plot type
that is being added to the repository.

Add sample data (less than 50 MB in size)
that can be used to create a reasonable plot example.

Use the pytest framework to generate tests.

Add an entry for the test in the
METplotpy/.github/workflows/unit_tests.yaml file
