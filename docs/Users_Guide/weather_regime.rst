*******************
Weather Regime plot
*******************

Description
===========

The **plot_weather_regime.py** script contains the plotting portion for
three scripts (**elbow.py, Calc_EOF.py**, and **K_means.py**)
These were originally created by Doug Miller at the University of Illinois.
A `METplus use case
<https://metplus.readthedocs.io/en/develop/generated/model_applications/s2s/UserScript_obsERA_obsOnly_WeatherRegime.html#sphx-glr-generated-model-applications-s2s-userscript-obsera-obsonly-weatherregime-py>`_
illustrates how to use this plot.

These files are used by the image comparison test:

* **obs_elbow.png**:  Run "plot_elbow" in **plot_weather_regime.py**
  to create this plot.

* **obs_eof.png**:  Run "plot_eof" in **plot_weather_regime.py**
  to create this plot.

* **obs_kmeans.png**:  Run "plot_K_means" in **plot_weather_regime.py**
  to create this plot.


Required Packages
=================

* Python 3.6.3

* Matplotlib 3.3.1

* Cartopy 0.17.1

* metcalcpy (see :numref:`METcalcpy_conda`)
  
* numpy

* cmocean

* psutil

* pytest

* pyyaml

* sklearn

* scipy

* eofs


How to Use
===========

Import plot_weather_regime into the script:

.. code-block:: ini

   import plot_weather_regime as pwr

For plot_elbow
______________

In the code, generate the following as numpy
arrays (except K, pot_title, and output_plotname).

**K:**  A range beginning at 1 and ending with the number of clusters used
in the weather regime analysis.

**d:**  A numpy array containing the differences between the curve and the
line.

**mi:**  A numpy array containing the location of the maximum distance.

**line:**  A numpy array representing the straight line from the sum of
squared differences for all clusters.

**curve:**  A numpy array containing the actual values of the sum of
squared distances.

**plot_title:**  A string that gives the name of the title of the plot.

**output_plotname:**  The full path and filename of the output plot file,
a **.png** version will be written.

For plot_eof
____________

In the code, generate the following as numpy arrays
(except wrnum, output_plotname, and plevels).

**eof:**  A numpy array containing the first 10 eof values.

**wrnum:**  An integer giving the number of weather regimes.

**variance_fractions:**  A numpy array containing the fractions of the
total variance accounted for by each EOF mode.

**lons:**  A numpy array of the longitude values under consideration.

**lats:**  A numpy array of the latitude values under consideration.

**output_plotname:**  The full path and filename of the output plot
file, a **.png** version will be written.

**plevels:**  A list containing integers of the contour levels used
in the plots.

For plot_K_means
________________

In the code, generate the following as numpy arrays
(except wrnum, output_plotname, and plevels).

**inputi:**  A numpy array containing the K means for the weather
regime classification.

**wrnum:**  An integer giving the number of weather regimes.

**lons:** A numpy array of the longitude values under consideration.

**lats:**  A numpy array of the latitude values under consideration.

**perc:**  A numpy array of the size wrnum containing the frequency of
occurrence of each cluster.

**output_plotname:**  The full path and filename of the output plot
file, a **.png** version will be written.

**plevels:** A list containing integers of the contour levels used in
the plots.

Invoke the plotting functions:

.. code-block:: ini

   pwr.plot_elbow(K,d,mi,line,curve,plot_title,plot_outname)

   pwr.plot_eof(eof,wrnum,variance_fractions,lons,lats,plot_outname,plevels)

   pwr.plot_K_means(kmeans,wrnum,lons,lats,perc,plot_outname,plevels)

The output will be **.png** version of the elbow line plot, eof contour map
plots, and weather regime map plots, if all three are requested. The output
will be located based on what was specified (path and name) in the
**output_plotname**.

