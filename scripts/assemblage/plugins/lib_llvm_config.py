#!/usr/bin/env python2
# -*- coding: UTF-8 -*-



import os
import subprocess


def find(parms):
    env = dict(os.environ)
    binpath = env.get('LLVM_CONFIG', 'llvm-config')
    deps = []
    ldflags = subprocess.check_output([binpath, '--libs', parms])
    flags = subprocess.check_output([binpath, '--cppflags', parms])
    return deps, flags, ldflags

