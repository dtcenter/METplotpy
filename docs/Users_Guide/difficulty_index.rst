*********************
Difficulty Index Plot
*********************

Description
===========

The difficulty index plot is a graphical representation of the expected difficulty of a decision based on a set of
forecasts (ensemble) of, e.g., significant wave height as a function of space and time. There are two basic factors
that can make a decision difficult. The first factor is the proximity of the ensemble mean forecast to a decision
threshold, e.g. 12 ft seas. If the ensemble mean is either much lower or much higher than the threshold, the
decision is easier; if it is closer to the threshold, the decision is harder. The second factor is the forecast
precision, or ensemble spread. The greater the spread around the ensemble mean, the more likely it is that there will
be ensemble members both above and below the decision threshold, making the decision harder. (A third factor that we
will not address here is undiagnosed systematic error, which adds uncertainty in a similar way to ensemble spread.)
The challenge is combining these factors into a continuous function that allows the user to assess relative risk.

The code for calculating and plotting the difficulty index was developed by Bill Campbell and Liz Satterfield of the
Navy Research Lab (NRL) and modified by NCAR.


For more information on calculating the difficulty index, please refer to this METplus use case:
`METviewer documentation
<https://metplus.readthedocs.io/en/develop/generated/model_applications/medium_range/UserScript_fcstGEFS_Difficulty_Index.html#sphx-glr-generated-model-applications-medium-range-userscript-fcstgefs-difficulty-index-py>`_.

Example
=======

Sample Data
___________

Sample data used to create an example difficulty index plot is
available in the METplotpy repository, where the difficulty index plot
code is located:

*$METPLOTPY_SOURCE/METplotpy/test/difficulty_index/swh_North_Pacific_5dy_ensemble.npz*

Copy this sample input file to your working directory, where you have read and write privileges:

.. code-block:: ini

    cp $METPLOTPY_SOURCE/METplotpy/test/difficulty_index/swh_North_Pacific_5dy_ensemble.npz $WORKING_DIR

Where *$METPLOTPY_SOURCE* is the directory where you saved the METplotpy source code and *$WORKING_DIR* is the
directory you created to store input data.


Required Packages
_________________

The following Python packages are necessary:

- Python 3.6
- numpy
- matplotlib 2.2.2 (minimum)
- scipy


Configuration Files
___________________

No configuration files are used to generate the difficulty index plot. All the settings for the plot are incorporated in
the mycolormaps.py and plot_difficulty_index.py code.  The example_difficulty_index.py script imports these modules to
create six sample plots.

METplus Configuration
=====================

Run from the Command Line
=========================

To generate the sample difficulty index plots, perform the following:

*  If using the conda environment, verify the conda environment
   is running and has has the required Python packages outlined in the **Required Packages** section above.


Where $METPLOTPY_SOURCE is the directory where you saved the METplotpy source code and $WORKING_DIR is the directory
you created earlier to store the sample input data.

* Change directory to the $WORKING_DIR:

    .. code-block:: ini

      cd $WORKING_DIR

where *$WORKING_DIR* is the directory where you copied all the necessary files (e.g. /home/users/someuser/working_dir).


* Run the following on the command line:

  .. code-block:: ini

    python example_difficulty_index.py


You will generate the following six files:

   **swh_North_Pacific_5dy_mean.png**:

     .. image:: swh_North_Pacific_5dy_mean.png

   **swh_North_Pacific_5dy_std.png**:

     .. image:: swh_North_Pacific_5dy_std.png

   **swh_North_Pacific_difficulty_index_10_00_feet.png**:

     .. image:: swh_North_Pacific_difficulty_index_10_00_feet.png

   **swh_North_Pacific_difficulty_index_11_00_feet.png**:

     .. image:: swh_North_Pacific_difficulty_index_11_00_feet.png

   **swh_North_Pacific_difficulty_index_12_00_feet.png**:

     .. image:: swh_North_Pacific_difficulty_index_12_00_feet.png

   **swh_North_Pacific_difficulty_index_9_00_feet.png**:

     .. image:: swh_North_Pacific_difficulty_index_9_00_feet.png


















