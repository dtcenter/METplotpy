"""
   Reads in the contents of the histogram_defaults.conf file, an INI file
   using the logic in produtil, which utilizes Python's ConfigParser.

"""

import sys

sys.path.insert(0, "../../../../../METplus/ush")
import produtil
import produtil.setup as ps
import config_metplus


def main():
    """
        Retrieve the values from the INI config file

        Input:


        Returns:



    """
    ps.setup(send_dbn=False, jobname='ReadHistogram_default_config')
    conf = config_metplus.setup()
    return conf


# def get_all_sections(config):
#     """ Retrieve all the sections in this configuration file
#
#         Input:
#         config:  a produtil config object representing the configuration defined
#                  in the user's configuration file(s).
#
#         Return:
#             a list of sections in the configuration file
#     """
#     return config_metplus.setup().sections



if __name__ == "__main__":
    print(sys.path)
    cf = main()

    print(cf)

