#!/usr/bin/env python2
# -*- coding: UTF-8 -*-




import os
import subprocess


__all__ = [
    'ALL_LIBRARY_PLUGINS',
]

def as_list(obj):
    if isinstance(obj, list):
        return obj
    return [obj]

def make_config_find(env_name, default_exec, cflags_params, cppflags_params, ldflags_params):
    def find(params):
        if params is None:
            params = []
        else:
            if isinstance(params, (str, unicode, )) and len(params) <= 0:
                params = []
        env = dict(os.environ)
        binpath = env.get(env_name, default_exec)
        deps = []
        implicit_files = []
        cflags = subprocess.check_output([binpath] + as_list(cflags_params) + params)
        cppflags = subprocess.check_output([binpath] + as_list(cppflags_params) + params)
        ldflags = subprocess.check_output([binpath] + as_list(ldflags_params) + params)
        return deps, implicit_files, cflags, cppflags, ldflags
    return find

ALL_LIBRARY_PLUGINS = {
    'pkg-config' : make_config_find('PKG_CONFIG' , 'pkg-config' , '--cflags', '--cflags'  , '--libs'),
    'llvm-config': make_config_find('LLVM_CONFIG', 'llvm-config', '--cflags', '--cxxflags', '--libs'),
    'fltk-config': make_config_find('FLTK_CONFIG', 'fltk-config', '--cflags', '--cflags'  , '--ldflags'),
    'odbc_config': make_config_find('ODBC_CONFIG', 'odbc_config', '--cflags', '--cflags'  , '--libs'),
    'wx-config'  : make_config_find('WX_CONFIG'  , 'wx-config'  , '--cflags', '--cxxflags', '--libs'),
}







