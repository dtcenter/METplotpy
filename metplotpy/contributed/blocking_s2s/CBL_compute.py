
"""
Purpose - Calculate the Central Blocking Latitude (CBL) for each season. The CBL is 
          defined as the latitude with the maximum high-pass Z500 variance 
          (varies with longitude). This represents the mid-latitude storm track. 

Input - File containing input data, 500-hPa Geopotential height, 
        in [YR,DAY,LAT,LON]. Make sure to specify lat lon limits of your domain of interest.

Output - File containing the CBL [YR, Lon]

@Author: Douglas E. Miller (dem2@illinois.edu)
         modified by DTCenter (08/2020) to separate computation of CBL from
         plotting of CBLs.
"""
#########################################
# Import Pakcages, may need to install some
#########################################
from pylab import *

from netCDF4 import Dataset
import CBL_plot as cp

def main(infile):
    monstr='DJF'

    lw = 2
    rc('axes',linewidth=1.5)
    # infile =  '../../test/cbl/Z500dayDJF.nc'
    # File location of Geopotential height data as [YR,DAY,LAT,LON]
    # Read in the data
    var = 'Z500'
    f1 = Dataset(infile, mode="r")
    H = f1.variables[var][:]
    f1.close()
    H = np.array(H)

    #intitlize lat and lon limits
    # Makes an array from 1980 - 2017
    yr=np.arange(1980,2018,1)

    #Create Latitude Weight based for NH
    cos = np.linspace(89,0,90)
    cos = cos * np.pi / 180.0
    way = np.cos(cos)
    way = np.sqrt(way)
    weightf = np.repeat(way[:,np.newaxis],360,axis=1)

    # Create lat and lon arrays, 1 degree
    # lons = np.linspace(0,359,360)
    lons = np.linspace(0,359,360)
    lats = np.linspace(89,0,90)

    ## 5-day running mean from data ("high pass")
    # Separate out lats so they are 0-90
    H = H[:,:,0:90,:]
    mh = np.zeros((H.shape))
    mh[mh==0]=np.nan
    m=2
    for i in np.arange(0,len(H[:,0,0,0]),1):
      temp = H[i,:,:,:]
      ml = np.zeros((temp.shape))
      ml[ml==0]=np.nan
      for d in np.arange(m,len(temp[:,0,0])-m,1):
        t1 = temp[d-m:d+m+1]
        ml[d] = np.nanmean(t1,axis=0)
      mh[i,:,:,:] = temp - ml

    ####Find latitude of maximum high-pass STD (CBL)
    mstd = np.nanstd(mh,axis=1)
    mhweight = mstd * weightf
    cbli = np.argmax(mhweight,axis=1)
    CBL = np.zeros((len(H[:,0,0,0]),len(lons)))
    for j in np.arange(0,len(yr),1):
      CBL[j,:] = lats[cbli[j,:]]

    ###Apply 9-degree moving average to smooth CBL profiles
    lt = len(lons)-1
    CBLf = np.zeros((len(H[:,0,0,0]),len(lons)))
    m=4
    for i in np.arange(0,len(CBL[0,:]),1):
      if i < m:
        temp1 = CBL[:,-m+i:-1]
        temp2 = CBL[:,-1:]
        temp3 = CBL[:,0:m+i+1]
        temp = np.concatenate((temp1,temp2),axis=1)
        temp = np.concatenate((temp,temp3),axis=1)
        CBLf[:,i] = np.nanmean(temp,axis=1).astype(int)
      elif i > (lt-m):
        temp1 = CBL[:,i-m:-1]
        temp2 = CBL[:,-1:]
        temp3 = CBL[:,0:m+i-lt]
        temp = np.concatenate((temp1,temp2),axis=1)
        temp = np.concatenate((temp,temp3),axis=1)
        CBLf[:,i] = np.nanmean(temp,axis=1).astype(int)
      else:
        temp = CBL[:,i-m:i+m+1]
        CBLf[:,i] = np.nanmean(temp,axis=1).astype(int)

    ###Plotting LTM CBL and Z500 variance
    CBLm = np.mean(CBLf,axis=0)
    mmstd=np.nanmean(mhweight,axis=0)
    plotfilename = "./CBL_" + monstr
    cp.create_cbl_plot(lons, lats, CBLm, mmstd, monstr, plotfilename)


if __name__ == "__main__":
    file1 = 'Z500dayDJF.nc'
    main(file1)






