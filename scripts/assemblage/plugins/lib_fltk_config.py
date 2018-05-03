#!/usr/bin/env python2
# -*- coding: UTF-8 -*-

import os
import subprocess


def find(parms):
    env = dict(os.environ)
    binpath = env.get('FLTK_CONFIG', 'fltk-config')
    deps = []
    ldflags = subprocess.check_output([binpath, '--ldflags', parms])
    flags = subprocess.check_output([binpath, '--cxxflags', parms])
    return deps, flags, ldflags
