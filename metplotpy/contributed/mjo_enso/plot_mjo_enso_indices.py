import numpy as np
import matplotlib.pyplot as plt

def plot_make_maki(make,maki,dates,plotname,plottype='png'):

     ymin = -8
     ymax = 3  

     plt.figure(figsize=(20,10))
     plt.plot(dates,make,'r')
     plt.plot(dates,maki,'b')
     plt.axhline(y=-0.5,color='r',linestyle='--')
     plt.axhline(y=-2,color='b',linestyle='--')
     plt.xlim([dates[0],dates[len(dates)-1]])
     #plt.xticks(time_year)
     plt.ylim([ymin,ymax])
     plt.grid();
     plt.legend(['MaKE','MaKI'], loc='best')
     plt.savefig(plotname+'.'+plottype,format=plottype)
 
