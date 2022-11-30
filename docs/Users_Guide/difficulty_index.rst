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

*$METPLOTPY_BASE/test/difficulty_index/swh_North_Pacific_5dy_ensemble.npz*

Copy this sample input file to your working directory, where you have read and write privileges:

.. code-block:: ini

    cp $METPLOTPY_BASE/test/difficulty_index/swh_North_Pacific_5dy_ensemble.npz $WORKING_DIR

Where *$METPLOTPY_BASE* is the directory where you saved the METplotpy source code and *$WORKING_DIR* is the
directory you created to store input data.


Required Packages
_________________

The following Python packages are necessary:

- Python 3.8
- numpy
- matplotlib 2.2.2 (minimum)
- scipy


Configuration Files
___________________

All the settings for the example difficulty index plot are incorporated in
the mycolormaps.py and plot_difficulty_index.py code.  The example_difficulty_index.py script imports these modules to
create six sample plots.  The location of where these plots are saved are determined by settings in the
example_difficulty_index.yaml configuration file:

.. literalinclude:: ../../test/difficulty_index/example_difficulty_index.yaml


Copy this config file from the directory where the source code was
saved to the working directory:

.. code-block:: ini

  cp $METPLOTPY_BASE/test/difficulty_index/example_difficulty_index.yaml $WORKING_DIR/example_difficulty_index.yaml


Modify the *input_filename* setting in the
*$METPLOTPY_BASE/test/difficulty_index/example_difficulty_index.yaml* file to
explicitly point to the *$METPLOTPY_BASE/test/difficulty_index*
directory (where the config file and sample data reside).
Replace the path */path/to/swh_North_Pacific_5dy_ensemble.npz* with the full path
*$METPLOTPY_BASE/test/difficulty_index/swh_North_Pacific_5dy_ensemble.npz*
(including replacing *$METPLOTPY_BASE* with the full path to the METplotpy
installation on the system).  Modify the *stat_fig_basename*
setting to point to the output path where the two statistics plots will be saved.
These plots will have a prefix of *swh_North_Pacific_5dy_*
Modify the *diff_fig_basename*
setting to point to the output path where the other four difficulty index plots will be saved.
These plots will have a prefix of *swh_North_Pacific_difficulty_index_*



METplus Configuration
=====================

Run from the Command Line
=========================

To generate the sample difficulty index plots, perform the following:

*  If using the conda environment, verify the conda environment
   is running and has has the required Python packages outlined in the **Required Packages** section above.


Where $METPLOTPY_BASE is the directory where you saved the METplotpy source code and $WORKING_DIR is the directory
you created earlier to store the sample input data.

* Change directory to the $WORKING_DIR:

    .. code-block:: ini

      cd $WORKING_DIR

where *$WORKING_DIR* is the directory where you copied all the necessary files (e.g. /home/users/someuser/working_dir).


* Run the following on the command line:

  .. code-block:: ini

    python ${METPLOTPY_BASE}/test/difficulty_index/example_difficulty_index.py example_difficulty_index.yaml


You will generate the following six files in the directories you specified for the
difficulty index and statistics plots:

**"Statistics plots"**

   **swh_North_Pacific_5dy_mean.png**:

     .. image:: swh_North_Pacific_5dy_mean.png

   **swh_North_Pacific_5dy_std.png**:

     .. image:: swh_North_Pacific_5dy_std.png

**"Difficulty Index" Plots**

   **swh_North_Pacific_difficulty_index_10_00_feet.png**:

     .. image:: swh_North_Pacific_difficulty_index_10_00_feet.png

   **swh_North_Pacific_difficulty_index_11_00_feet.png**:

     .. image:: swh_North_Pacific_difficulty_index_11_00_feet.png


   **swh_North_Pacific_difficulty_index_12_00_feet.png**:

     .. image:: swh_North_Pacific_difficulty_index_12_00_feet.png

   **swh_North_Pacific_difficulty_index_9_00_feet.png**:

     .. image:: swh_North_Pacific_difficulty_index_9_00_feet.png


















