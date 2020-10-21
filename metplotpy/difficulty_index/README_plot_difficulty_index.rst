Difficulty Index
================
Written by Bill Campbell and Liz Satterfield (NRL)
Modified by Lindsay Blank (NCAR)
Date Modified: October 21, 2020

Background
==========

The overall aim of this work is to graphically represent the expected difficulty of a decision based on a set of forecasts (ensemble) of, e.g., significant wave height as a function of space and time. There are two basic factors that can make a decision difficult. The first factor is the proximity of the ensemble mean forecast to a decision threshold, e.g. 12 ft seas. If the ensemble mean is either much lower or much higher than the threshold, the decision is easier; if it is closer to the threshold, the decision is harder. The second factor is the forecast precision, or ensemble spread. The greater the spread around the ensemble mean, the more likely it is that there will be ensemble members both above and below the decision threshold, making the decision harder. (A third factor that we will not address here is undiagnosed systematic error, which adds uncertainty in a similar way to ensemble spread.) The challenge is combing these factors into a continuous function that allows the user to assess relative risk.


Pre-requisites:
===============
Python packages:
---------------
- numpy
- matplotlib
- scipy

Python 3.6

Input files:
------------
**Need to find out from NRL**

Input Required:
===============
The function to plot the difficulty index is as follows: 

def plot_field(field, lats, lons, vmin, vmax,
        xlab, ylab, cmap, clab, title):

The following is required to plot the difficulty index:
#. **field:** Difficulty index values (see METcalcpy resources for how to calculate the difficulty index)
#. **lats:** Latitude values
#. **lons:** Longitude values
#. **vmin:** Minimum value on the colorbar
#. **vmax:** Maximum value on the colorbar
#. **xlab:** x-axis label
#. **ylab:** y-axis label
#. **cmap:** Color map for plot
#. **clab:** Label for colorbar
#. **title:** Plot title


Output generated:
=================
Calling the plot_field function in plot_difficulty_index.py will return a difficulty index plot.

How to run:
==========
Run a 'pip install -e .' in $METplotpy to add metplotpy to the path. To call plot_difficulty_index, add the following import statement to the script:

'from metplotpy.difficulty_index.plot_difficulty_index import plot_field'

To see an example, please look at the following:
$METplotpy/test/difficulty_index/example_difficulty_index.py
