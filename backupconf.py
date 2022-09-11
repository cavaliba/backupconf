
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
import socket

ARGS = {}
CONF = {}
VERSION = "backupconf - Version 1.0 - 2022/09/04 - cavaliba.com"

# ----

TEMPLATE_CONF="""
---
# cavaliba.com / backupconf / conf.yml

# usually  in /opt/backupconf/conf.yml

prefix: vmdemo
backupdir: /tmp/backup
tmpdir: /tmp/test

paths:
  # use ** pattern for any subdir (recursive)
  # use .* pattern for any dotfiles (.dotfile)
  # use *.* pattern for any file
  - invalid/path/not/absolute
  - /path/not/exist/should/fail/safe
  - /home/phil/Documents/dev/backupconf/testdata/*.conf
  - /home/phil/Documents/dev/backupconf/testdata/**/*.conf
  - /home/phil/Documents/dev/backupconf/testdata/.*
  - /home/phil/Documents/dev/backupconf/testdata/**/.*
  - /home/phil/Documents/dev/backupconf/testdata/**/*.*
  - /home/phil/Documents/dev/backupconf/testdata/dir1/subdir1/**/*.*
  - /etc/bash.bashrc
  - /etc/fstab
  - /etc/exports
  - /etc/passwd
  - /etc/shadow
  - /etc/group
  - /etc/crontab
  - /etc/cron.d/**/*/*
  - /etc/cron.weekly/**/*/*
  - /etc/cron.daily/**/*/*
  - /etc/cron.hourly/**/*/*
  - /etc/os-release
  - /etc/hostname
  - /etc/timezone
  - /etc/aliases
  - /etc/networks
  - /etc/network/**/*.*
  - /etc/hosts.allow
  - /etc/profile
  - /etc/logrotate.conf
  - /etc/logrotate.d/**/*.*
  - /etc/resolv.conf
  - /etc/sysctl.conf
  - /etc/sysctl.d/**/*.*
  - /etc/rsyslog.conf
  - /etc/rsyslog.d/**/*.*
  - /etc/sudoers
  - /etc/sudoers.d/**/*.*
  - /etc/ca-certificates/**/*.*
  - /etc/redis/**/*.*
  - /etc/httpd/**/*.*
  - /etc/nginx/**/*.*
  - /etc/apache2/**/*.*
  - /etc/mysql/**/*.*
  - /etc/postgresql/**/*.*
  - /etc/elasticsearch/**/*
  - /etc/kibana/**/*.*
  - /etc/samba/**/*.*
  - /opt/cmt/conf.yml
  - /opt/cmt/conf.d/**/*.*
"""

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

    parser.add_argument('--debug', help='verbose/debug output',
                         action='store_true', required=False)

    parser.add_argument('--list', '-l', help='list identified files, no backup',
                        action='store_true', required=False)

    parser.add_argument('--template', help='print a conf template',
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

    # TODO : option for printing an empty config template
    if ARGS["template"]:
        print(TEMPLATE_CONF)
        sys.exit()




    logit("-" * 80)
    logit("Starting backupconf...")

    configfile = ARGS["conf"]
    try:
        CONF = conf_load_file(configfile)
        logit("config file loaded : " + configfile)
    except:        
        print("Could not load config file " + configfile)
        sys.exit()


    # Prepare dirs and names

    backupprefix = CONF.get("prefix", socket.gethostname())
    backupprefix += "_"
    instance = backupprefix + datetime.datetime.today().strftime("%Y%m%d_%H%M%S")
    backupdir = CONF["backupdir"]
    tmprootdir = CONF["tmpdir"]
    # create a tmpdir for that RUN inside tmprootdir
    tmpdir = tmprootdir + "/" + instance
    
    logit("prefix    : " + backupprefix)
    logit("instance  : " + instance)
    logit("backupdir : " + backupdir)
    logit("tmprootdir: " + tmprootdir)
    logit("tmpdir: " + tmpdir)

    # create tmpdir 
    if not ARGS['list']:
        try:
            os.makedirs(tmpdir, mode = 0o700, exist_ok = True) 
            logit("make tmpdir : " + tmpdir)
        except Exception as e:
            logit("FATAL : failed to make tmpdir " + tmpdir + " - " + str(e) )
            sys.exit(0)

    # TODO  : add a maxitem / maxsize CONF parameter


    # Main loop

    item_count_global = 0
    skip_count = 0
    error_count = 0

    # LOOP over patterns in CONF
    for pattern in CONF["paths"]:

        logit("Path: " + pattern)

        if pattern[0] != "/":
            logit("  ERROR - Not an absolute PATH (should start with a /)")
            error_count += 1
            continue


        item_count_pattern = 0

        # LOOP over items in glob(pattern)
        for item in glob.glob(pattern, recursive=True):

            srcpath = os.path.dirname(item)
            destpath = tmpdir + srcpath
            debug("---")
            debug("item : " + item)
            debug("srcpath : " + srcpath)
            debug("destpath : " + destpath)

            item_count_pattern += 1
            
            if ARGS['list']:
                logit("  LIST - " + item)
            else:

                # HACK : sometimes glob returns a DIR
                if os.path.isdir(item):
                    destpath = tmpdir + item
                    debug("not a file ; mkdir instead and continue : " + item)
                    debug("recomputed destpath : " + destpath)
                    os.makedirs(destpath, mode = 0o700, exist_ok = True) 
                    continue

                # create target dir if missing
                try:
                    os.makedirs(destpath, mode = 0o700, exist_ok = True) 
                    debug("mkdir : " + destpath)

                except Exception as e:
                    error_count += 1
                    logit("ERROR - failed to makedir : " + destpath + " - " + str(e) )
                    continue

                # copy: replace / overwrite if existing
                try:
                    shutil.copy(item, destpath, follow_symlinks=True)
                except Exception as e:
                    error_count += 1
                    logit("ERROR - failed to copy " + item + " to " + destpath + " - " + str(e) )
                    continue
                
                logit("  COPIED - " + item + " to " + destpath)

        # stat/count by pattern
        if item_count_pattern > 0:
            item_count_global += item_count_pattern
            if ARGS['list']:
                logit("  " + str(item_count_pattern) + " items found")
            else:
                logit("  " + str(item_count_pattern) + " items copied")
        else:
            logit("  SKIPPED - Nothing / not found")
            skip_count += 1


    if ARGS['list']:
        logit("TOTAL   : " + str(item_count_global) + " items found")
        logit("SKIPPED : " + str(skip_count) )
        logit("ERRORS  : " + str(error_count) )
        sys.exit()


    # tar, gzip 
    archive_name = backupdir + "/" + instance
    archive_mode = "gztar"   #tar
    archive_extension = "tar.gz"
    archive_file = archive_name + "." + archive_extension

    shutil.make_archive(archive_name, archive_mode, tmpdir)
    logit("Archive built : " + archive_name + " - mode " + archive_mode)
    logit("Archive chmod : " + archive_file + " : 600")
    os.chmod(archive_file, 0o600)

    # TODO : crypt

    # TODO : copy to secondary locations

    # cleanup tmpdir
    try:
        shutil.rmtree(tmpdir)
        logit("remove tmpdir : " + tmpdir)
    except Exception as e:
        logit("ERROR - failed to remove tmpdir : " + tmpdir + " - " + str(e) )

    # TODO : cleanup TMPROOTDIR

    # TODO : cleanup older backups : number, or age or size

    # global stats
    logit("TOTAL   : " + str(item_count_global) + " items copied")
    logit("SKIPPED : " + str(skip_count) )
    logit("ERRORS  : " + str(error_count) )

    # TODO : compute duration
    # TODO : display archive size
    # TODO : prepare/send cmt event
    # TODO : display keywords with color
    # TODO : ARG option to display an empty / example CONF

    logit("Done")



