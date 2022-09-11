backupconf - cavaliba.com
=========================

(c) cavaliba.com 2020-2022  - Version 1.1 - 2022/09/11

Simple backup tool for Linux / OS and related config files.


Setup

    * download in /opt/backupconf/
    * virtualenv, prerequisite (pyinstaller binaries soon)
    * create a simple config : python3 backupconf.py --template > /opt/backupconf/conf.yml
    * customize
    * create /tmp/backupconftmp  (workdir)
    * create /var/backupconf/    (backups / archives)
    * chmod  / chown 600 to protect sensitive files and backups
    * perform a test : sudo python3 backupconf.py --list -c conf.yml
    * perform a run : sudo python3 backupconf.py -c conf.yml
    * inspect backup archive in /var/backupconf/
    * add a cron entry to run every few hours



Standard config


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
        backupdir: /tmp/backupconf

        # tmp root directory where tmp archives are created 
        # must exist before run (not created by backupconf)
        # must be protected from unauthorized access (root/700 if run by root)
        # WARNING: must be **dedicated** to backupconf (emptied after run)
        tmprootdir: /tmp/backupconftmp

        paths:
        # use ** pattern for any subdir (recursive)
        # use .* pattern for any dotfiles (.dotfile)
        # use *.* pattern for any file

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

