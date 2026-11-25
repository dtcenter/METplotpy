****************************************
Generate Tests and Add to GitHub Actions
****************************************

Create a subdirectory under the *test* directory
(e.g., *test/<newplot>* where **<newplot>** is replaced with the
name of the plot type that is being added to the repository.)

Add sample data (see applicable information in the
`Adding a New Plot
<https://metplus.readthedocs.io/projects/metplotpy/en/develop/Contributors_Guide/new_plot.html#adding-a-new-plot>`_
section).

Use the pytest framework to generate tests. For more information, review
this `pytest documentation <https://docs.pytest.org/en/7.2.x>`_.

Add an entry for the test in the
*.github/workflows/unit_tests.yaml* file.

Installing the Test Dependencies
================================

pytest is not installed with METplotpy by default. From the top of the
repository, in your active conda (or virtual) environment, install METplotpy
in editable mode with the ``test`` extra. This installs the packages listed in
**requirements.txt** plus pytest:

.. code-block:: console

    $ pip install -e ".[test]"

METplotpy and its tests import ``metcalcpy``, which is **not** installed by the
command above. Install METcalcpy before running the tests (see
:ref:`METcalcpy_conda`). The GitHub Actions workflows install it from the
``develop`` branch:

.. code-block:: console

    $ git clone https://github.com/dtcenter/METcalcpy
    $ git -C METcalcpy checkout develop
    $ pip install -e METcalcpy

To check test coverage, also install ``pytest-cov``:

.. code-block:: console

    $ pip install pytest-cov
