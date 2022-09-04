
# backupconf.py
# (c) cavaliba.com 2022


# usage
# python3 backupconf.py --conf myconf.yml



import os
import sys
import yaml

# import time
import datetime
import signal
# import json
# import requests
# import hashlib
import argparse
import shutil
import glob


ARGS = {}
CONF = {}
VERSION = "backupconf - Version 1.0 - 2022/09/04 - cavaliba.com"


# -----------------
def logit(line):
    now = datetime.datetime.today().strftime("%Y/%m/%d - %H:%M:%S")
    print(now + ' : ' + line)

def debug(*items):
    if ARGS['debug']:
        print('DEBUG :', ' '.join(items))

# -----------------
def timeout_handler(signum, frame):
    # raise Exception("Timed out!")
    print("Timed out ! (max_execution_time)")
    sys.exit()

# -----------------
def conf_load_file(config_file):

    with open(config_file) as f:
        conf = yaml.load(f, Loader=yaml.SafeLoader)
        # print(json.dumps(CONF, indent=2))

    # verify content
    if conf is None:
        return {}

    return conf

# -----------------
class BlankLinesHelpFormatter(argparse.HelpFormatter):
   def _split_lines(self, text, width):
        return super()._split_lines(text, width) + ['']

def parse_arguments(myargs):

    parser = argparse.ArgumentParser(description='backupconf by Cavaliba.com', formatter_class = BlankLinesHelpFormatter)

    parser.add_argument('--version', '-v', help='display current version',
                        action='store_true', required=False)

    # parser.add_argument('--cron', help='equiv to report, pager_enable, persist, short output',
    #                     action='store_true', required=False)

    parser.add_argument('--conf', '-c', help='specify yaml config file',
                        action='store', required=True)

    # parser.add_argument('--debug', help='verbose/debug output',
    #                     action='store_true', required=False)

    parser.add_argument('--list', '-l', help='list identified files, no backup',
                        action='store_true', required=False)


    r = parser.parse_args(myargs)
    return vars(r)
    
   

# ------------
# Main entry
# ------------


if __name__ == "__main__":

    if not sys.version_info >= (3, 6):
        logit("Should use Python >= 3.6")
        sys.exit()

    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(60)   # seconds


    ARGS = parse_arguments(sys.argv[1:])

    if ARGS["version"]:
        print(VERSION)
        sys.exit()

    logit("Starting backupconf...")

    configfile = ARGS["conf"]
    try:
        CONF = conf_load_file(configfile)
        logit("config file loaded : " + configfile)
    except:        
        print("Could not load config file " + configfile)
        sys.exit()


    #dest = "/tmp/test"
    tmpdir = CONF["tmpdir"]

    for pattern in CONF["paths"]:
        logit("Path: " + pattern)

        if pattern[0] != "/":
            logit("  SKIPPED - Not an absolute PATH (should start with a /)")
            continue


        for item in glob.glob(pattern, recursive=True):
            srcpath = os.path.dirname(item)
            destpath = tmpdir + srcpath
            
            if ARGS['list']:
                logit("  LIST - " + item)
            else:
                # create target dir if missing
                os.makedirs(destpath, mode = 0o700, exist_ok = True) 
                # copy: replace / overwrite if existing
                shutil.copy(item, destpath, follow_symlinks=False)
                logit("  COPIED - " + item)



    # tar, gzip 






    logit("Done")