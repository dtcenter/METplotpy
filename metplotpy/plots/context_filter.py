import logging
import getpass

class ContextFilter(logging.Filter):
    '''
        This is a filter which injects contextual information into the log.
        The contextual information is the user name but can also be other useful
        information about the user such as the IP address from which this code is
        being run.

    '''

    def filter(self, record):
       '''
         Args:
           @param record: data struction containing the user information.
         Returns: True when the record is created
       '''

       # Retrieve the user id of the user running the code.
       record.user = getpass.getuser()
       return True
