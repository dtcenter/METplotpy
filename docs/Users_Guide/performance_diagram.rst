Performance diagram
===========================================

Description
~~~~~~~~~~~

Performance diagrams are used to show the relationship between categorical statistics, with 
axes representing detection and success(1 - false alarm) rates Roebber, 2009).  
The simplest input to the performance diagram is the MET contingency table statistics (CTS) 
output.  This output can be produced by many of the MET tools (Point-Stat, Grid-Stat, etc.). 


There are several reference lines on the performance diagram.  The dashed lines that radiate
from the origin are lines of equal frequency bias.  Labels for the frequency bias amount are
at the end of each line. The diagonal represents a perfect frequency bias score of 1.  Curves
of equal Critical Success Index (CSI) connect the top of the plot to the right side.  CSI 
amounts are listed to the right side of the plot, with better values falling closer to the top.

Example
~~~~~~~

**Sample Data**

The sample data used to create these plots is available in the METplotpy repository, where the 
performance diagram scripts are located:

$METPLOTPY_SOURCE/METplotpy/metplotpy/plots/plot_20200317_151252.data

The data is text output from MET in columnar format.



**Configuration Files**


