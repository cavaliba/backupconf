# backupconf.py
# (c) cavaliba.com 2022

# usage
# python3 backupconf.py --conf myconf.yml

# TODO-2 : crypt / GPG support
# TODO-2 : copy to secondary locations
# TODO-2 : compute duration
# TODO-2 : display archive size
# TODO-2 : prepare/send cmt event
# TODO-2  : add a maxitem / maxsize CONF parameter
# TODO-2 : rotate / cleanup older backups : number, or age or size


import os
import sys
import yaml
import datetime
import signal
import argparse
import shutil
import glob
import socket

ARGS = {}
CONF = {}
VERSION = "backupconf - Version 1.1 - 2022/09/11 - cavaliba.com"

# ----

TEMPLATE_CONF="""
---
# cavaliba.com / backupconf / conf.yml

# usually in /opt/backupconf/conf.yml
# with chown root / chmod 600
# launched by root cron : 15 7,13,18,23 * * * /opt/backupconf/backupconf -c /opt/backupconf/conf.yml >> /var/log/backupconf.log

# default : hostname
prefix: vmdemo

# target for archives created by backupconf
# must be dedicated to backupconf
# must exist before run (not created by backupconf)
# must be protected from unauthorized access (root/700 if run by root)
# cleanup / rotation / export must be performed separately from backupconf
backupdir: /var/backupconf

# tmp root directory where tmp archives are created 
# must exist before run (not created by backupconf)
# must be protected from unauthorized access (root/700 if run by root)
# WARNING: must be **dedicated** to backupconf (emptied after run)
tmprootdir: /tmp/backupconftmp

paths:
# use ** pattern for any subdir (recursive)
# use .* pattern for any dotfiles (.dotfile)
# use * pattern for any file

# - invalid/path/not/absolute
# - /path/not/exist/should/fail/safe

- /etc/bash.bashrc
- /etc/fstab
- /etc/exports
- /etc/passwd
- /etc/shadow
- /etc/group
- /etc/crontab
- /etc/cron.d/**/*
- /etc/cron.weekly/**/*
- /etc/cron.daily/**/*
- /etc/cron.hourly/**/*
- /var/spool/cron/crontabs/*
- /etc/os-release
- /etc/hostname
- /etc/timezone
- /etc/aliases
- /etc/networks
- /etc/network/**/*
- /etc/hosts.allow
- /etc/profile
- /etc/logrotate.conf
- /etc/logrotate.d/**/*
- /etc/resolv.conf
- /etc/sysctl.conf
- /etc/sysctl.d/**/*
- /etc/rsyslog.conf
- /etc/rsyslog.d/**/*
- /etc/sudoers
- /etc/sudoers.d/**/*
- /etc/ca-certificates/**/*

- /etc/redis/**/*
- /etc/httpd/**/*
- /etc/nginx/**/*
- /etc/apache2/**/*
- /etc/mysql/**/*
- /etc/postgresql/**/*.*
- /etc/elasticsearch/**/*
- /etc/kibana/**/*
- /etc/samba/**/*

- /opt/cmt/conf.yml
- /opt/cmt/conf.d/**/*
"""

# -----------------
def logit(line):
    now = datetime.datetime.today().strftime("%Y/%m/%d - %H:%M:%S")
    print(now + ' : ' + line)

def debug(*items):
    now = datetime.datetime.today().strftime("%Y/%m/%d - %H:%M:%S")
    if ARGS['debug']:
        print(now + ' : ' + 'DEBUG :', ' '.join(items))

# -----------------
def timeout_handler(signum, frame):
    # raise Exception("Timed out!")
    print("Timed out ! (max_execution_time)")
    sys.exit()

# -----------------
def conf_load_file(config_file):

    with open(config_file) as f:
        conf = yaml.load(f, Loader=yaml.SafeLoader)

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

    parser.add_argument('--showconf', help='print the configuration and exit',
                        action='store_true', required=False)

    parser.add_argument('--template', help='print a configuration template and exit',
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

    # print an empty config template
    if ARGS["template"]:
        print(TEMPLATE_CONF)
        sys.exit()

    configfile = ARGS["conf"]
    try:
        CONF = conf_load_file(configfile)
    except:        
        print("Could not load config file " + configfile)
        sys.exit()

    # print an empty config template
    if ARGS["showconf"]:
        print(yaml.dump(CONF))
        sys.exit()

    logit("-" * 80)
    logit("config    : " + configfile)


    # Prepare dirs and names

    backupprefix = CONF.get("prefix", socket.gethostname())
    backupprefix += "_"
    logit("prefix    : " + backupprefix)


    instance = backupprefix + datetime.datetime.today().strftime("%Y%m%d_%H%M%S")
    logit("instance  : " + instance)

    backupdir = CONF["backupdir"]
    if not os.path.isdir(backupdir):
        print("FATAL : backupdir missing : " + backupdir)
        sys.exit(0)     
    logit("backupdir : " + backupdir)

    tmprootdir = CONF["tmprootdir"]
    if not os.path.isdir(tmprootdir):
        print("FATAL : tmpdir missing : " + tmprootdir)
        sys.exit(0) 
    logit("tmprootdir: " + tmprootdir)

    # create a tmpdir for that RUN inside tmprootdir
    tmpdir = tmprootdir + "/" + instance
    if not ARGS['list']:
        try:
            os.makedirs(tmpdir, mode = 0o700, exist_ok = True) 
            logit("tmpdir    : " + tmpdir)
        except Exception as e:
            logit("FATAL : failed to make tmpdir " + tmpdir + " - " + str(e) )
            sys.exit(0)

    logit("--- Starting loop over paths ...")

    # --------------------------------
    # Main loop over patterns in CONF
    # --------------------------------

    item_count_global = 0
    skip_count = 0
    error_count = 0

    for pattern in CONF["paths"]:

        debug("Starting with PATH: " + pattern)

        if pattern[0] != "/":
            logit("  ERROR - Not an absolute PATH (should start with a /)")
            error_count += 1
            continue

        if ARGS['list']:
            logit("PATH : " + pattern)

        item_count_pattern = 0

        # ------------------------------------
        # LOOP over items in glob(pattern)
        # ------------------------------------

        for item in glob.glob(pattern, recursive=True):

            srcpath = os.path.dirname(item)
            destpath = tmpdir + srcpath
            debug("item : " + item)
            debug("srcpath : " + srcpath)
            debug("destpath : " + destpath)

            item_count_pattern += 1
            
            if ARGS['list']:
                logit("  LIST - item : " + item)
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
                
                debug("copy - " + item + " to " + destpath)

        # stat/count by pattern
        item_count_global += item_count_pattern
        if ARGS['list']:
            logit("  " + str(item_count_pattern) + " items found")
        else:
            if item_count_pattern > 0:
                    logit(pattern + " - " + str(item_count_pattern) + " items found and copied")
            else:
                logit("SKIP : " + pattern + " not found or empty")
                skip_count += 1

    logit("--- loop done.")

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
    logit("archive built : " + archive_name + " - mode " + archive_mode)
    logit("archive chmod : " + archive_file + " : 600")
    os.chmod(archive_file, 0o600)


    # remove tmpdir
    try:
        shutil.rmtree(tmpdir)
        logit("remove tmpdir : " + tmpdir)
    except Exception as e:
        logit("ERROR - failed to remove tmpdir : " + tmpdir + " - " + str(e) )

    # cleanup TMPROOTDIR - old / interrupted backups, files, dirs are removed !
    folder = tmprootdir
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
                logit("cleanup - " + file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
                logit("cleanup - " + file_path)
        except Exception as e:
            logit('cleanup - Failed to delete %s. Reason: %s' % (file_path, e))
        #for item in glob.glob(tmprootdir + "/**/*", recursive=True):
        #    print("CLEANUP TODO : " + item)



    # global stats
    logit("TOTAL   : " + str(item_count_global) + " items copied")
    logit("SKIPPED : " + str(skip_count) )
    logit("ERRORS  : " + str(error_count) )

    logit("Done")



