#!/usr/bin/env python2
# -*- coding: UTF-8 -*-



import os
import subprocess


def find(parms):
    env = dict(os.environ)
    binpath = env.get('LLVM_CONFIG', 'llvm-config')
    deps = []
    implicit_files = []
    ldflags = subprocess.check_output([binpath, '--libs', parms])
    cflags = subprocess.check_output([binpath, '--cflags', parms])
    cppflags = subprocess.check_output([binpath, '--cxxflags', parms])
    return deps, implicit_files, cflags, cppflags, ldflags

