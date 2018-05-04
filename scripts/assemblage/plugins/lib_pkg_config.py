#!/usr/bin/env python2
# -*- coding: UTF-8 -*-


import os
import subprocess


def find(parms):
    env = dict(os.environ)
    binpath = env.get('PKG_CONFIG', 'pkg-config')
    deps = []
    implicit_files = []
    ldflags = subprocess.check_output([binpath, '--libs', parms])
    flags = subprocess.check_output([binpath, '--cflags', parms])
    cflags = cppflags = flags
    return deps, implicit_files, cflags, cppflags, ldflags

