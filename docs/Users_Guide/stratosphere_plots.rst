*******************
Stratosphere plots
*******************

Description
===========

The **stratosphere_plots.py** script contains the plotting portion for
three Stratosphere use cases.  One use case creates a ME plot in latitude and pressure,
another which creates ME and RMSE plots for lead time and pressure, and a third which 
creates two phase diagrams and a time series of U for at 50mb and 30mb.
The three METplus use cases, illustrate how to use these plotting scripts for `zonal mean biases
<https://metplus.readthedocs.io/en/develop/generated/model_applications/s2s_stratosphere/UserScript_fcstGFS_obsERA_StratosphereBias.html#sphx-glr-generated-model-applications-s2s-stratosphere-userscript-fcstgfs-obsera-stratospherebias-py>`_ , creating bias and RMSE for `polar cap temperature and polar vortex U <https://metplus.readthedocs.io/en/develop/generated/model_applications/s2s_stratosphere/UserScript_fcstGFS_obsERA_StratospherePolar.html#sphx-glr-generated-model-applications-s2s-stratosphere-userscript-fcstgfs-obsera-stratospherepolar-py>`_ and creating `phase diagrams and time series for QBO <https://metplus.readthedocs.io/en/develop/generated/model_applications/s2s_stratosphere/UserScript_fcstGFS_obsERA_StratosphereQBO.html#sphx-glr-generated-model-applications-s2s-stratosphere-userscript-fcstgfs-obsera-stratosphereqbo-py>`_

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

* **ERA_GFS_QBO_circuits.png**:  Run "plot_qbo_phase_circuits" in **stratosphere_plots.py**
  to create this plot.

* **ERA5_QBO_PhaseSpace.png**:  Run "plot_qbo_phase_space" in **stratosphere_plots.py**
  to create this plot.

* **ERA_GFS_timeseries_30mb_u_201710_201802.png**:  Run "plot_u_timeseries" in **stratosphere_plots.py**
  to create this plot.

* **ERA_GFS_timeseries_50mb_u_201710_201802.png**:  Run "plot_u_timeseries" in **stratosphere_plots.py**
  to create this plot.


Required Packages
=================

* Python

* Matplotlib

* metcalcpy (see :numref:`METcalcpy_conda`)

* metdataio
  
* numpy

* xarray

* pandas

* cmocean

* pyyaml


How to Use
===========

Import stratosphere_plots into the script:

.. code-block:: ini

   from stratosphere_plots import plot_zonal_bias,plot_polar_bias,plot_polar_rmse, plot_qbo_phase_circuits,plot_qbo_phase_space,plot_u_timeseries

For plot_zonal_bias
-------------------

In the code, generate the following as numpy
arrays (except outfile, ptitle, and plevs).

**lats:**  A numpy array of the latitude values under consideration.

**levels:** A numpy array of the pressure level values under consideration.

**bias:**  A numpy array containing the bias.

**obar:**  A numpy array of the size wrnum containing the frequency of
occurrence of each cluster.

**outfile:**  The full path and filename of the output plot
file, a **.png** version will be written.

**ptitle:** A string containing the title of the plot.

**plevs:** A list containing integers of the contour levels used in
plotting the obs climatology.

For plot_polar_bias
-------------------

In the code, generate the following as numpy arrays
(except outfile, ptitle, and plevs).

**leads:**  A numpy array containing the forecast lead times.

**levels:**  A numpy array of the pressure level values under consideration.

**pdata:**  A numpy array containing the bias.

**outfile:**  The full path and filename of the output plot
file, a **.png** version will be written.

**ptitle:**  A string containing the title of the plot.

**plevs:**  A list containing floats of the contour levels used in
plotting.

For plot_polar_rmse
-------------------

In the code, generate the following as numpy arrays
(except outfile, ptitle, and plevs).

**leads:**  A numpy array containing the forecast lead times.

**levels:**  A numpy array of the pressure level values under consideration.

**pdata:**  A numpy array containing the RMSE.

**outfile:**  The full path and filename of the output plot
file, a **.png** version will be written.

**ptitle:**  A string containing the title of the plot.

**plevs:**  A list containing floats of the contour levels used in
plotting.

For plot_qbo_phase_circuits
---------------------------

In the code, generate the following as numpy arrays
(except inits, periods, and outfile).

**inits:**  A listing of datetimes that are the start date for each plot.

**periods:**  An integer containing the number of days to plot from the inits.

**rean_qbo_pcs:**  An xarray dataarray containing the projected daily 
zonal winds for the observations.

**rfcst_qbo_pcs:**  An xarray dataarray containing the projected 
daily zonal winds for the model.

**outfile:**  The full path and filename of the output plot
file, a **.png** version will be written.

For plot_qbo_phase_space
------------------------

In the code, generate the following as numpy arrays
(except ptitle and outfile).

**rean_qbo_pcs:**  An xarray dataarray containing the projected 
daily zonal winds. 

**eofs:**  An xarray dataarray containing the EOFs.

**ptitle:**  A string containing the title of the plot.

**outfile:**  The full path and filename of the output plot
file, a **.png** version will be written.

For plot_u_timeseries
---------------------

In the code, generate the following as numpy arrays
(except ptitle and outfile).

**obs_dt:**  A numpy array of datetimes for the observations.

**obs_u:**  A numpy array containing U wind values for 
the observations.

**fcst_dt:**  A numpy array of datetimes for the forecasts.

**fcst_u:**  A numpy array containing U wind values for 
the forecasts.

**ptitle:**  A string containing the title of the plot.

**outfile:**  The full path and filename of the output plot
file, a **.png** version will be written.

Invoke the plotting functions:

.. code-block:: ini

   plot_zonal_bias(lats,levels,bias,obar,outfile,ptitle,plevs)

   plot_polar_bias(leads,levels,pdata,outfile,ptitle,plevs)

   plot_polar_rmse(leads,levels,pdata,outfile,ptitle,plevs)

   plot_qbo_phase_circuits(inits,periods,rean_qbo_pcs,rfcst_qbo_pcs,outfile)

   plot_qbo_phase_space(rean_qbo_pcs,eofs,ptitle,outfile)

   plot_u_timeseries(obs_dt,obs_u,fcst_dt,fcst_u,ptitle,outfile)

The output will be **.png** version of all requested plots and will
be located based on what was specified (path and name) in the
**outfile**.

