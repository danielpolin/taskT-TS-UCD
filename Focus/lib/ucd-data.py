#/usr/bin/env ccs-script
import sys
import time
import os
import logging
import datetime
from argparse import ArgumentParser
from java.time import Duration
import java.lang.Exception as JException

from org.lsst.ccs.scripting import CCS

from ccs import aliases
from ccs import proxies
from ccs import versions
from ccs import configs
import config

# Temporary work around for problems with CCS responsiveness
CCS.setDefaultTimeout(Duration.ofSeconds(30))

class WarningFilter(object):

    def filter(self, log_record): 
        return log_record.levelno != logging.WARNING

def main(cfgfile, run=None):

    ## Set up logging
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    log_format = logging.Formatter("%(asctime)s %(levelname)s: %(message)s", 
                                   datefmt = "%Y-%m-%d %H:%M:%S")

    ## Set up handler for command line
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(logging.DEBUG)
    stream_handler.setFormatter(log_format)
    logger.addHandler(stream_handler)

    ## Set up handler for daily observing log file
    ih = CCS.attachSubsystem("ucd-ih")
    rootdir = ih.sendSynchCommand("getConfigurationParameterValue imageHandler/ImageHandlingConfig FITSRootDirectory")
    today = datetime.date.today().strftime("%Y%m%d")
    if not os.path.exists(os.path.join(rootdir, today)):
        os.makedirs(os.path.join(rootdir, today))

    obsfile_handler = logging.FileHandler(os.path.join(rootdir, today, '{0}_acquisition.log'.format(today)))
    obsfile_handler.setLevel(logging.INFO)
    obsfile_handler.addFilter(WarningFilter())
    obsfile_handler.setFormatter(log_format)
    logger.addHandler(obsfile_handler)

    ## Set up handler for global log file
    homedir = os.path.expanduser('~')
    globalfile_handler = logging.FileHandler(os.path.join(homedir, 'data_acquisition.log'))
    globalfile_handler.setLevel(logging.DEBUG)
    globalfile_handler.setFormatter(log_format)
    logger.addHandler(globalfile_handler)

    ## Write config versions to cwd
    if run:
        fp = CCS.attachProxy('ucd-fp')
        time.sleep(10.0)
        versions.write_versions(fp)
        configs.write_config(fp, ['Sequencer', 'Rafts'])

    ## Parse config file and execute data acquisition
    try:
        cfg = config.parseConfig(cfgfile)
        config.execute(cfg, {"run" : run})
    except (JException, Exception):
        logger.exception("Fatal error occurred in data acquisition.")

if __name__ == '__main__':

    parser = ArgumentParser(sys.argv[0], add_help=False)
    parser.add_argument('cfgfile', type=str)
    parser.add_argument('--run', type=str, default=None)

    args = parser.parse_args()
    main(args.cfgfile, args.run)
