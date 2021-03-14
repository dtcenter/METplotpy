README

**Required packages**

Python 3.6.3

Matplotlib 3.3.1

Cartopy 0.17.1

metcalcpy  (see README of github.com/dtcenter/METcalcpy for instructions to install locally into your conda env)

numpy

cmocean

psutil

pytest

pyyaml

sklearn

scipy

eofs

*(Please add any other packages to this list, if we accidentally omitted any)*

**Description**

plot_weather_regime.py contains the plotting portion for 3 scripts (elbow.py, Calc_EOF.py, and K_means.py)
that were originally created Doug Miller at the 
script created by Univerity of Illinois.

These files are used by the image comparison test:

* **obs_elbow.png**  
    is the plot that should be generated when you run plot_elbow in plot_weather_regime.py


* **obs_eof.png** 
    is the plot that should be generated when you run plot_eof in plot_weather_regime.py


* **obs_kmeans.png**
    is the plot that should be generated when you run plot_K_means in plot_weather_regime.py


**How to use**

Import plot_weather_regime in your script like so:

*import plot_weather_regime as pwr*

**For plot_elbow**

In your code, generate the following as numpy arrays
(except K, pot_title, and output_plotname):

* **K**:
    a range beginning at 1 and ending with the number of clusters used in the 
    weather regime analysis

* **d**:
    a numpy array containing the differences between the curve and the line

* **mi**:
    a numpy array containing the location of the maximum distance

* **line**:
    a numpy array representing the straight line from the sum of squared difference for all clusters

* **curve**:
    a numpy array containing the actual values of sum of squared distances

* **plot_title**:
    A string that gives the name of the title of the plot

* **output_plotname**:
    The full path and filename of the output plot file, a .png
    version is written

**For plot_eof**

In your code, generate the following as numpy arrays
(except wrnum, output_plotname, and plevels):

* **eof**:
    a numpy array containing the first 10 eof values 

* **wrnum**:
    an integer giving the number of weather regimes

* **variance_fractions**:
    a numpy array containing the fractions of the total variance accounted for by each EOF mode

* **lons**:
    a numpy array of the longitude values under consideration

* **lats**:
    a numpy array of the latitude values under consideration

* **output_plotname**:
    The full path and filename of the output plot file, a .png
    version is written

* **plevels**:
    a list containing integers of the contour levels used in the plots

**For plot_K_means**

In your code, generate the following as numpy arrays
(except wrnum, output_plotname, and plevels):

* **inputi**:
    a numpy array containing the K means for the weather regime classification

* **wrnum**:
    an integer giving the number of weather regimes

* **lons**:
    a numpy array of the longitude values under consideration

* **lats**:
    a numpy array of the latitude values under consideration

* **perc**:
    a numpy array of the size wrnum containing the frequency of occurrence
    of each cluster

* **output_plotname**:
    The full path and filename of the output plot file, a .png
    version is written

* **plevels**:
    a list containing integers of the contour levels used in the plots


**Invoke the plotting functions**
    | pwr.plot_elbow(K,d,mi,line,curve,plot_title,plot_outname)
    | pwr.plot_eof(eof,wrnum,variance_fractions,lons,lats,plot_outname,plevels)
    | pwr.plot_K_means(kmeans,wrnum,lons,lats,perc,plot_outname,plevels)


**Output**
    A .png version of the elbow line plot, eof contour map plots, and weather
    regime map plots if all three are requeste.  The output will be located 
    based on what you specified (path and name) in the **output_plotname**.
