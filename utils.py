#! /usr/bin/python
# -*- coding: utf-8 -*-

import os
import sys
from subprocess import Popen, PIPE


def check_postgresql_running():
    #Check if PostgreSQL server is running
    status = Popen(['/etc/init.d/postgresql', 'status'], stdout=PIPE, stderr=PIPE)
    (stdoutdata, err) = status.communicate()
    if stdoutdata[-5:-1] == 'down':
        sys.exit("\nPlease, start PostgreSQL server.")


def make_dir(path):
    """Create a directory if it does not already exist
    """
    if not os.path.exists(path):
        os.makedirs(path)
