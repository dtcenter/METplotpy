"""
    Example of how to use the produtil + Python ConfigParser solution to handling INI-type
    configuration files in the METplotpy repository.
"""

from os import path
import sys
# sys.path.append("/Users/minnawin/METplus/ush")
# sys.path.append(path.abspath('.../../METplus/ush'))
sys.path.insert(0, '/Users/minnawin/METplus/ush')
sys.path.insert(0,'/Users/minnawin/METplus/ush/produtil')
# sys.path.remove("/Users/minnawin/METplus/ush")
# sys.path.remove("/Users/minnawin/feature_13_yaml_check/METplotpy/proto")
import produtil.setup

if __name__ == "__main__":

    print(sys.path)
    produtil.setup.setup(send_dbn=False, jobname='TestProdutilForMETplotpy')
