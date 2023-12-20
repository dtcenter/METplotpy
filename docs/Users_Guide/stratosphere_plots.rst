*******************
Stratosphere plots
*******************

Description
===========

The **stratosphere_plots.py** script contains the plotting portion for
two Stratosphere use cases, one which creates a ME plot in latitude and pressure
and another which creates ME and RMSE plots for lead time and pressure
Two METplus use cases, illustrate how to use this plot.  One runs `zonal mean biases
<https://metplus.readthedocs.io/en/develop/generated/model_applications/s2s/UserScript_obsERA_obsOnly_WeatherRegime.html#sphx-glr-generated-model-applications-s2s-userscript-fcstgfs-obsera-stratospherebias-py>`_
and another creates bias and RMSE for `polar cap temperature and polar vortex U <https://metplus.readthedocs.io/en/develop/generated/model_applications/s2s/UserScript_obsERA_obsOnly_WeatherRegime.html#sphx-glr-generated-model-applications-s2s-userscript-fcstgfs-obsera-stratospherepolar-py>`_

These files are used by the image comparison test:

* **GFS_ERA_ME_2018_02_zonal_mean_T.png**:  Run "plot_zonal_bias" in **stratosphere_plots.py.py**
  to create this plot.

* **GFS_ERA_ME_2018_02_zonal_mean_U.png**:  Run "plot_zonal_bias" in **stratosphere_plots.py**
  to create this plot.

* **ME_2018_02_polar_cap_T.png**:  Run "plot_polar_bias" in **stratosphere_plots.py**
  to create this plot.

* **ME_2018_02_polar_vortex_U.png**: Rn "plot_polar_bias" in **stratosphere_plots.py**
  to create this plot.

* **RMSE_2018_02_polar_cap_T.png**:  Run "plot_polar_rmse" in **stratosphere_plots.py**
  to create this plot.

* **RMSE_2018_02_polar_vortex_U.png**:  Run "plot_polar_rmse" in **stratosphere_plots.py**
  to create this plot.


Required Packages
=================

* Python

* Matplotlib

* metcalcpy (see :numref:`METcalcpy_conda`)

* metdataio
  
* numpy

* pandas

* cmocean

* pyyaml


How to Use
===========

Import stratosphere_plots into the script:

.. code-block:: ini

   from stratosphere_plots import plot_zonal_bias,plot_polar_bias,plot_polar_rmse

For plot_zonal_bias
-------------------

In the code, generate the following as numpy
arrays (except outfile, ptitle, and plevels).

**lats:**  A numpy array of the latitude values under consideration.

**levels:** A numpy array of the pressure level values under consideration.

**bias:**  A numpy array containing the bias.

**obar:**  A numpy array of the size wrnum containing the frequency of
occurrence of each cluster.

**outfile:**  The full path and filename of the output plot
file, a **.png** version will be written.

**ptitle:** A string containing the title of the plot.

**plevels:** A list containing integers of the contour levels used in
plotting the obs climatology.

For plot_polar_bias
-------------------

In the code, generate the following as numpy arrays
(except wrnum, output_plotname, and plevels).

**leads:**  A numpy array containing the forecast lead times.

**levels:**  A numpy array of the pressure level values under consideration.

**pdata:**  A numpy array containing the bias.

**outfile:**  The full path and filename of the output plot
file, a **.png** version will be written.

**ptitle:**  A string containing the title of the plot.

**plevs:**  A list containing floats of the contour levels used in
plotting

For plot_polar_rmse
-------------------

In the code, generate the following as numpy arrays
(except wrnum, output_plotname, and plevels).

**leads:**  A numpy array containing the forecast lead times.

**levels:**  A numpy array of the pressure level values under consideration.

**pdata:**  A numpy array containing the bias.

**outfile:**  The full path and filename of the output plot
file, a **.png** version will be written.

**ptitle:**  A string containing the title of the plot.

**plevs:**  A list containing floats of the contour levels used in
plotting

Invoke the plotting functions:

.. code-block:: ini

   plot_zonal_bias(lats,levels,bias,obar,outfile,ptitle,plevs)

   plot_polar_bias(leads,levels,pdata,outfile,ptitle,plevs)

   plot_polar_rmse(leads,levels,pdata,outfile,ptitle,plevs)

The output will be **.png** version of all requested plots and will
be located based on what was specified (path and name) in the
**output_plotname**.

