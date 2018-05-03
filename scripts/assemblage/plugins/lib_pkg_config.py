#!/usr/bin/env python2
# -*- coding: UTF-8 -*-


import os
import subprocess


def find(parms):
    env = dict(os.environ)
    binpath = env.get('PKG_CONFIG', 'pkg-config')
    deps = []
    ldflags = subprocess.check_output([binpath, '--libs', parms])
    flags = subprocess.check_output([binpath, '--cflags', parms])
    return deps, flags, ldflags

