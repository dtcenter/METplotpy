import os
import re
import sys
import logging
import collections
import datetime
import shutil
from os.path import dirname, realpath

from produtil.config import ProdConfig
import produtil.fileop
import met_util as util

"""!Creates the initial METplotpy directory structure,
loads information into each job.

This module is used to create the initial METplotpy conf file in the
first METplotpy job via the metplotpy.config_launcher.launch().
The metplotpy.config_launcher.load() then reloads that configuration.
The launch() function does more than just create the conf file though.
It creates several initial files and  directories and runs a sanity check
on the whole setup.

The METplotpyConfig class is used in place of a produtil.config.ProdConfig
throughout the METplotpy system.  It can be used as a drop-in replacement
for a produtil.config.ProdConfig, but has additional features needed to
support sanity checks, and initial creation of the METplotpy system.
"""

'''!@var __all__
All symbols exported by "from metplotpy.launcher import *"
'''
__all__ = ['load', 'launch', 'parse_launch_args',
           'METplotpyConfig']
# Note: This is just a developer reference comment, in case we continue
# extending the metplotpy capabilities, by following hwrf patterns.
# These metplotpy configuration variables map to the following
# HWRF variables.
# METPLUS_BASE == HOMEmetplus, OUTPUT_BASE == WORKmetplus
# METPLUS_CONF == CONFmetplus, METPLUS_USH == USHmetplus
# PARM_BASE == PARMmetplus

'''!@var METPLOTPY_BASE
The METplotpy installation directory
'''
METPLOTPY_BASE = None

'''!@var METPLUS_BASE
The METplus installation directory
'''
METPLUS_BASE = None

'''!@var METPLUS_USH
The ush/ subdirectory of the METplus installation directory
'''
METPLUS_USH = None

'''!@var PARM_BASE
The parameter directory
'''
PARM_BASE = None

if os.environ.get('METPLUS_PARM_BASE', ''):
    PARM_BASE = os.environ['METPLUS_PARM_BASE']

# Based on METPLUS_BASE, Will set METPLUS_USH, or PARM_BASE if not
# already set in the environment.
METPLOTPY_BASE = dirname(dirname(realpath(__file__)))
METPLUS_BASE = os.path.join(METPLOTPY_BASE, "../../../METplus")
USHguess = os.path.join(METPLUS_BASE, 'ush')
PARMguess = os.path.join(METPLUS_BASE, 'parm')
if os.path.isdir(USHguess) and os.path.isdir(PARMguess):
    if METPLUS_USH is None:
        METPLUS_USH = USHguess
    if PARM_BASE is None:
        PARM_BASE = PARMguess

# For METplus, this is assumed to already be set.
if METPLUS_USH not in sys.path:
    sys.path.append(METPLUS_USH)


# def parse_launch_args(args,usage,logger,PARM_BASE=None):
# This is intended to be use to gather all the conf files on the
# command line, along with overide options on the command line.
# This includes the default conf files metplotpy.conf, metplotpy.override.conf
# along with, -c some.conf and any other conf files...
# These are than used by def launch to create a single metplotpy final conf file
# that would be used by all tasks.
def parse_launch_args(args, usage, filename, logger, baseinputconfs):
    """!Parsed arguments to scripts that launch the METplus system.

    This is the argument parser for the config_metplotpy.py
    script.  It parses the arguments (in args).
    If something goes wrong, this function calls
    sys.exit(1) or sys.exit(2).

    Options:
    * section.variable=value --- set this value in this section, no matter what
    * /path/to/file.conf --- read this conf file after the default conf files.

    Later conf files override earlier ones.  The conf files read in
    are:
    * metplotpy.conf

    @param args the script arguments, after script-specific ones are removed
    @param usage a function called to provide a usage message
    @param filename the module from which this was called
    @param logger a logging.Logger for log messages"""

    # stub
    # if test for something fails:
    #    usage(filename,logger)

    parm = os.path.realpath(PARM_BASE)

    # Files in this list, that don't exist or are empty,
    # will be silently ignored.
    # infiles=[ os.path.join(parm, 'metplotpy.conf'),
    #          os.path.join(parm, 'metplotpy.override.conf')
    #         ]
    infiles = list()
    for filename in baseinputconfs:
        # Check for entries that begin with metplus_config, and apply the
        # full path
        fname_match = re.match(r'^metplus_config.*')
        if fname_match:
            infiles.append(os.path.join(parm, fname_match.group(0)))
        else:
            # These are the METplotpy default config files which
            # already have the full path indicated.
            infiles.append(filename)

    moreopt = collections.defaultdict(dict)

    if args is None:
        return (parm, infiles, moreopt)

    # Now look for any option and conf file arguments:
    bad = False
    for iarg in range(len(args)):
        m = re.match(r'''(?x)
          (?P<section>[a-zA-Z][a-zA-Z0-9_]*)
           \.(?P<option>[^=]+)
           =(?P<value>.*)$''', args[iarg])
        if m:
            logger.info('Set [%s] %s = %s' % (
                m.group('section'), m.group('option'),
                repr(m.group('value'))))
            moreopt[m.group('section')][m.group('option')] = m.group('value')
        elif os.path.exists(args[iarg]):
            infiles.append(args[iarg])
        elif os.path.exists(os.path.join(parm, args[iarg])):
            infiles.append(os.path.join(parm, args[iarg]))
        else:
            bad = True
            logger.error('%s: invalid argument.  Not an config option '
                         '(a.b=c) nor a conf file.' % (args[iarg],))
    if bad:
        sys.exit(2)

    for file in infiles:
        if not os.path.exists(file):
            logger.error(file + ': conf file does not exist.')
            sys.exit(2)
        elif not os.path.isfile(file):
            logger.error(file + ': conf file is not a regular file.')
            sys.exit(2)
        elif not produtil.fileop.isnonempty(file):
            logger.warning(
                file + ': conf file is empty.  Will continue anyway.')
    return (parm, infiles, moreopt)


# This is intended to be used to create and write a final conf file
# that is used by all tasks.
# METplotpy tasks need to be able to run stand-alone
# so each task needs to be able to initialize the conf files.
# conf files are processed in the order they exist in the file_list
# so each successive element overwrites the previous.
def launch(file_list, moreopt, cycle=None, init_dirs=True,
           prelaunch=None):
    for filename in file_list:
        if not isinstance(filename, str):
            raise TypeError('First input to metplotpy.config.for_initial_job '
                            'must be a list of strings.')

    conf = METplotpyConfig()
    logger = conf.log()

    # set config variable for current time
    conf.set('config', 'CLOCK_TIME', datetime.datetime.now().strftime('%Y%m%d%H%M%S'))

    # Read in and parse all the conf files.
    for filename in file_list:
        conf.read(filename)
        logger.info("%s: Parsed this file" % (filename,))

    # Overriding or passing in specific conf items on the command line
    # ie. config.NEWVAR="a new var" dir.SOMEDIR=/override/dir/path
    # If spaces, seems like you need double quotes on command line.
    if moreopt:
        for section, options in moreopt.items():
            if not conf.has_section(section):
                conf.add_section(section)
            for option, value in options.items():
                logger.info('Override: %s.%s=%s'
                            % (section, option, repr(value)))
                conf.set(section, option, value)

    # All conf files and command line options have been parsed.
    # So lets set and add specific log variables to the conf object
    # based on the conf log template values.
    _set_logvars(conf)

    # Determine if final METPLOTPY_CONF file already exists on disk.
    # If it does, use it instead.
    confloc = conf.getloc('METPLOTPY_CONF')

    # Place holder for when workflow is developed in METplus.
    # rocoto does not initialize the dirs, it returns here.
    # if not init_dirs:
    #    if prelaunch is not None:
    #        prelaunch(conf,logger,cycle)
    #    return conf

    # Initialize the output directories
    produtil.fileop.makedirs(conf.getdir('OUTPUT_BASE', logger), logger=logger)
    # A user my set the confloc METPLUS_CONF location in a subdir of OUTPUT_BASE
    # or even in another parent directory altogether, so make thedirectory
    # so the metplotpy_final.conf file can be written.
    if not os.path.exists(realpath(dirname(confloc))):
        produtil.fileop.makedirs(realpath(dirname(confloc)), logger=logger)

    # set METPLUS_BASE conf to location of scripts used by METplus
    # warn if user has set METPLUS_BASE to something different
    # in their conf file
    user_metplus_base = conf.getdir('METPLUS_BASE', METPLUS_BASE)
    if realpath(user_metplus_base) != realpath(METPLUS_BASE):
        logger.warning('METPLUS_BASE from the conf files has no effect.' + \
                       ' Overriding to ' + METPLUS_BASE)

    conf.set('dir', 'METPLUS_BASE', METPLUS_BASE)

    # do the same for PARM_BASE
    user_parm_base = conf.getdir('PARM_BASE', PARM_BASE)
    if realpath(user_parm_base) != realpath(PARM_BASE):
        logger.error('PARM_BASE from the config ({}) '.format(user_parm_base) + \
                     'differs from METplus parm base ({}). '.format(PARM_BASE))
        logger.error('Please remove PARM_BASE from any config file. Set the ' + \
                     'environment variable METPLUS_PARM_BASE to change where ' + \
                     'the METplus wrappers look for config files.')
        exit(1)

    conf.set('dir', 'PARM_BASE', PARM_BASE)

    # print config items that are set automatically
    for var in ('METPLUS_BASE', 'PARM_BASE'):
        expand = conf.getdir(var)
        logger.info('Setting [dir] %s to %s' % (var, expand))

    # Place holder for when workflow is developed in METplus.
    # if prelaunch is not None:
    #    prelaunch(conf,logger,cycle)

    # writes the METPLUS_CONF used by all tasks.
    logger.info('METPLUS_CONF: %s written here.' % (confloc,))
    with open(confloc, 'wt') as f:
        conf.write(f)

    return conf


def load(filename):
    """!Loads the METplusConfig created by the launch() function.

    Creates an METplusConfig object for a METplus workflow that was
    previously initialized by metplotpy.config_launcher.launch.
    The only argument is the name of the config file produced by
    the launch command.

    @param filename The metplotpy*.conf file created by launch()"""

    conf = METplotpyConfig()
    conf.read(filename)
    return conf


def set_conf_file_path(conf_file):
    return _set_conf_file_path(conf_file)


# This is meant to be used with the -c option in METplus
# for backward compatability, since users using the -c option
# are not required to add path information and the previous
# constants object found it since it was pulled in via the import
# statement and the parm directory was defined in the PYTHONPATH
def _set_conf_file_path(conf_file):
    """Do not call this directly.  It is an internal implementation
    routine. It is only used internally and is called when adding an
    additional conf using the -c command line option.

    Adds the path information to the conf file if there isn't any.
    """
    parm = os.path.realpath(PARM_BASE)

    # Determine if add_conf_file has path information /path/to/file.conf
    # If not head than there is no path information, only a filename,
    # so assUme the conf file is in the parm directory, and add that
    # parm path information
    head, tail = os.path.split(conf_file)
    if not head:
        new_conf_file = os.path.join(parm, conf_file)
        return new_conf_file

    return conf_file


def _set_logvars(config, logger=None):
    """!Sets and adds the LOG_METPLUS and LOG_TIMESTAMP
       to the config object. If LOG_METPLOTPY was already defined by the
       user in their conf file. It expands and rewrites it in the conf
       object and the final file.
       conf file.
       Args:
           @param config:   the config instance
           @param logger: the logger, optional
    """

    if logger is None:
        logger = config.log()

    # LOG_TIMESTAMP_TEMPLATE is not required in the conf file,
    # so lets first test for that.
    log_timestamp_template = config.getstr('config', 'LOG_TIMESTAMP_TEMPLATE', '')
    if log_timestamp_template:
        # Note: strftime appears to handle if log_timestamp_template
        # is a string ie. 'blah' and not a valid set of % directives %Y%m%d,
        # it does return the string 'blah', instead of crashing.
        # However, I'm still going to test for a valid % directive and
        # set a default. It probably is ok to remove the if not block pattern
        # test, and not set a default, especially if causing some unintended
        # consequences or the pattern is not capturing a valid directive.
        # The reality is, the user is expected to have entered a correct
        # directive in the conf file.
        # This pattern is meant to test for a repeating set of
        # case insensitive %(AnyAlphabeticCharacter), ie. %Y%m ...
        # The basic pattern is (%+[a-z])+ , %+ allows for 1 or more
        # % characters, ie. %%Y, %% is a valid directive.
        # (?i) case insensitive, \A begin string \Z end of string
        if not re.match(r'(?i)\A(?:(%+[a-z])+)\Z', log_timestamp_template):
            logger.warning('Your LOG_TIMESTAMP_TEMPLATE is not '
                           'a valid strftime directive: %s' % repr(log_timestamp_template))
            logger.info('Using the following default: %Y%m%d%H')
            log_timestamp_template = '%Y%m%d%H'
        date_t = datetime.datetime.now()
        if config.getbool('config', 'LOG_TIMESTAMP_USE_DATATIME', False):
            if util.is_loop_by_init(config):
                date_t = datetime.datetime.strptime(config.getstr('config',
                                                                  'INIT_BEG'),
                                                    config.getstr('config',
                                                                  'INIT_TIME_FMT'))
            else:
                date_t = datetime.datetime.strptime(config.getstr('config',
                                                                  'VALID_BEG'),
                                                    config.getstr('config',
                                                                  'VALID_TIME_FMT'))
        log_filenametimestamp = date_t.strftime(log_timestamp_template)
    else:
        log_filenametimestamp = ''

    log_dir = config.getdir('LOG_DIR')

    # NOTE: LOG_METPLUS or metplotpylog is meant to include the absolute path
    #       and the metplotpylog_filename,
    # so metplotpylog = /path/to/metplotpylog_filename

    # if LOG_METPLOTPY =  unset in the conf file, means NO logging.
    # Also, assumes the user has included the intended path in LOG_METPLOTPY.
    user_defined_log_file = None
    if config.has_option('config', 'LOG_METPLUS'):
        user_defined_log_file = True
        # strinterp will set metplotpylog to '' if LOG_METPLUS =  is unset.
        metplotpylog = config.strinterp('config', '{LOG_METPLUS}',
                                        LOG_TIMESTAMP_TEMPLATE=log_filenametimestamp)

        # test if there is any path information, if there is, assUme it is as intended,
        # if there is not, than add log_dir.
        if metplotpylog:
            if os.path.basename(metplotpylog) == metplotpylog:
                metplotpylog = os.path.join(log_dir, metplotpylog)
    else:
        # No LOG_METPLUS in conf file, so let the code try to set it,
        # if the user defined the variable LOG_FILENAME_TEMPLATE.
        # LOG_FILENAME_TEMPLATE is an 'unpublished' variable - no one knows
        # about it unless you are reading this. Why does this exist ?
        # It was from my first cycle implementation. I did not want to pull
        # it out, in case the group wanted a stand alone metplotpy log filename
        # template variable.

        # If metplotpylog_filename includes a path, python joins it intelligently.
        # Set the metplotpy log filename.
        # strinterp will set metplotpylog_filename to '' if LOG_FILENAME_TEMPLATE =
        if config.has_option('config', 'LOG_FILENAME_TEMPLATE'):
            metplotpylog_filename = config.strinterp('config', '{LOG_FILENAME_TEMPLATE}',
                                                     LOG_TIMESTAMP_TEMPLATE=log_filenametimestamp)
        else:
            metplotpylog_filename = ''
        if metplotpylog_filename:
            metplotlog = os.path.join(log_dir, metplotpylog_filename)
        else:
            metplotpylog = ''

    # Adding LOG_TIMESTAMP to the final configuration file.
    logger.info('Adding: config.LOG_TIMESTAMP=%s' % repr(log_filenametimestamp))
    config.set('config', 'LOG_TIMESTAMP', log_filenametimestamp)

    # Setting LOG_METPLOTPY in the configuration object
    # At this point LOG_METPLOTPY will have a value or '' the empty string.
    if user_defined_log_file:
        logger.info('Replace [config] LOG_METPLOTPY with %s' % repr(metplotpylog))
    else:
        logger.info('Adding: config.LOG_METPLOTPY=%s' % repr(metplotpylog))
    # expand LOG_METPLOTPY to ensure it is available
    config.set('config', 'LOG_METPLOTPY', metplotpylog)


class METplotpyConfig(ProdConfig):
    """!A replacement for the produtil.config.ProdConfig used throughout
    the METplus and METplotpy system.  You should never need to instantiate one of
    these --- the launch() and load() functions do that for you.  This
    class is the underlying implementation of most of the
    functionality described in launch() and load()"""

    def __init__(self, conf=None):
        """!Creates a new METplotpyConfig
        @param conf The configuration file."""
        super(METplotpyConfig, self).__init__(conf)
        self._cycle = None
        self._logger = logging.getLogger('metplotpy')
        # config.logger is called in wrappers, so set this name
        # so the code doesn't break
        self.logger = self._logger

        # get the OS environment and store it
        self.env = os.environ.copy()

        # TODO: does this do anything?
        logger = self._logger

    ##@var _cycle
    # The cycle for this METPLOTPY run.

    # Overrides method in ProdConfig
    def log(self, sublog=None):
        """!returns a logging.Logger object

        Returns a logging.Logger object.  If the sublog argument is
        provided, then the logger will be under that subdomain of the
        "metplotpy" logging domain.  Otherwise, this METplotpylauncher's logger
        (usually the "metplot" domain) is returned.
        @param sublog the logging subdomain, or None
        @returns a logging.Logger object"""
        if sublog is not None:
            with self:
                return logging.getLogger('metplotpy.' + sublog)
        return self._logger

    def sanity_check(self):
        """!Runs nearly all sanity checks.

        Runs simple sanity checks on the METplotpy installation directory
        and configuration to make sure everything looks okay.  May
        throw a wide variety of exceptions if sanity checks fail."""
        logger = self.log('sanity.checker')

    # override get methods to perform additional error checking
    def getraw(self, sec, opt, default='', count=0):
        """ parse parameter and replace any existing parameters
            referenced with the value (looking in same section, then
            config, dir, and os environment)
            returns raw string, preserving {valid?fmt=%Y} blocks
            Args:
                @param sec: Section in the conf file to look for variable
                @param opt: Variable to interpret
                @param default: Default value to use if config is not set
                @param count: Counter used to stop recursion to prevent infinite
            Returns:
                Raw string
        """
        count = count + 1
        if count >= 10:
            return ''

        in_template = super(METplotpyConfig, self).getraw(sec, opt, default)
        out_template = ""
        in_brackets = False
        for index, character in enumerate(in_template):
            if character == "{":
                in_brackets = True
                start_idx = index
            elif character == "}":
                var_name = in_template[start_idx + 1:index]
                var = None
                if self.has_option(sec, var_name):
                    var = self.getraw(sec, var_name, default, count)
                elif self.has_option('config', var_name):
                    var = self.getraw('config', var_name, default, count)
                elif self.has_option('dir', var_name):
                    var = self.getraw('dir', var_name, default, count)
                elif self.has_option('filename_templates', var_name):
                    var = self.getraw('filename_templates', var_name, default, count)
                elif var_name[0:3] == "ENV":
                    var = os.environ.get(var_name[4:-1])

                if var is None:
                    out_template += in_template[start_idx:index + 1]
                else:
                    out_template += var
                in_brackets = False
            elif not in_brackets:
                out_template += character

        return out_template

    def check_default(self, sec, name, default):
        """!helper function for get methods, report error and exit if
            default is not set """
        if default is None:
            msg = 'Requested conf [{}] {} was not set in config file'.format(sec, name)
            if self.logger:
                self.logger.error(msg)
            else:
                print('ERROR: {}'.format(msg))
            exit(1)

        # print debug message saying default value was used
        msg = "Setting [{}] {} to default value: {}.".format(sec,
                                                             name,
                                                             default)
        if self.logger:
            self.logger.debug(msg)
        else:
            print('DEBUG: {}'.format(msg))

        # set conf with default value so all defaults can be added to
        #  the final conf and warning only appears once per conf item
        #  using a default value
        self.set(sec, name, default)

    def getexe(self, exe_name, default=None, morevars=None):
        """!Wraps produtil exe with checks to see if option is set and if
            exe actually exists"""
        if not self.has_option('exe', exe_name):
            msg = 'Requested [exe] {} was not set in config file'.format(exe_name)
            if self.logger:
                self.logger.error(msg)
            else:
                print('ERROR: {}'.format(msg))
            exit(1)

        exe_path = super(METplotpyConfig, self).getexe(exe_name)

        full_exe_path = shutil.which(exe_path)
        if full_exe_path is None:
            msg = 'Executable {} does not exist at {}'.format(exe_name, exe_path)
            if self.logger:
                self.logger.error(msg)
            else:
                print('ERROR: {}'.format(msg))
            exit(1)

        # set config item to full path to exe and return full path
        self.set('exe', exe_name, full_exe_path)
        return full_exe_path

    def getdir(self, dir_name, default=None, morevars=None, taskvars=None):
        """!Wraps produtil getdir and reports an error if it is set to /path/to"""
        if not self.has_option('dir', dir_name):
            self.check_default('dir', dir_name, default)
            dir_path = default
        else:
            dir_path = super(METplotpyConfig, self).getdir(dir_name)

        if '/path/to' in dir_path:
            msg = 'Directory {} is set to or contains /path/to.'.format(dir_name) + \
                  ' Please set this to a valid location'
            if self.logger:
                self.logger.error(msg)
            else:
                print('ERROR: {}'.format(msg))
            exit(1)

        return dir_path

    def getdir_nocheck(self, dir_name, default=None):
        super(METplotpyConfig, self).getdir(dir_name, default=default)

    def getstr(self, sec, name, default=None, badtypeok=False, morevars=None, taskvars=None):
        """!Wraps produtil getstr to gracefully report if variable is not set
            and no default value is specified"""
        if self.has_option(sec, name):
            return super(METplotpyConfig, self).getstr(sec, name, default=default, badtypeok=badtypeok,
                                                       morevars=morevars, taskvars=taskvars)

        # config item was not found
        self.check_default(sec, name, default)
        return default

    def getbool(self, sec, name, default=None, badtypeok=False, morevars=None, taskvars=None):
        """!Wraps produtil getbool to gracefully report if variable is not set
            and no default value is specified"""
        if self.has_option(sec, name):
            return super(METplotpyConfig, self).getbool(sec, name, default=default, badtypeok=badtypeok,
                                                        morevars=morevars, taskvars=taskvars)

        # config item was not found
        self.check_default(sec, name, default)
        return default

    def getint(self, sec, name, default=None, badtypeok=False, morevars=None, taskvars=None):
        """!Wraps produtil getint to gracefully report if variable is not set
            and no default value is specified"""
        if self.has_option(sec, name):
            return super(METplotpyConfig, self).getint(sec, name, default=default, badtypeok=badtypeok,
                                                       morevars=morevars, taskvars=taskvars)

        # config item was not found
        self.check_default(sec, name, default)
        return default

    def getfloat(self, sec, name, default=None, badtypeok=False, morevars=None, taskvars=None):
        """!Wraps produtil getfloat to gracefully report if variable is not set
            and no default value is specified"""
        if self.has_option(sec, name):
            return super(METplotpyConfig, self).getfloat(sec, name, default=default, badtypeok=badtypeok,
                                                         morevars=morevars, taskvars=taskvars)

        # config item was not found
        self.check_default(sec, name, default)
        return default

    def getseconds(self, sec, name, default=None, badtypeok=False, morevars=None, taskvars=None):
        """!Converts time values ending in H, M, or S to seconds"""
        if self.has_option(sec, name):
            # convert value to seconds
            # Valid options match format 3600, 3600S, 60M, or 1H
            value = super(METplotpyConfig, self).getstr(sec, name, default=default, badtypeok=badtypeok,
                                                        morevars=morevars, taskvars=taskvars)
            regex_and_multiplier = {r'(-*)(\d+)S': 1,
                                    r'(-*)(\d+)M': 60,
                                    r'(-*)(\d+)H': 3600,
                                    r'(-*)(\d+)': 1}
            for reg, mult in regex_and_multiplier.items():
                match = re.match(reg, value)
                if match:
                    if match.group(1) == '-':
                        mult = mult * -1
                    return int(match.group(2)) * mult

            # if value is not in an expected format, error and exit
            msg = '[{}] {} does not match expected format. '.format(sec, name) + \
                  'Valid options match 3600, 3600S, 60M, or 1H'
            if self.logger:
                self.logger.error(msg)
            else:
                print('ERROR: {}'.format(msg))

            exit(1)

        # config item was not found
        self.check_default(sec, name, default)
        return default
