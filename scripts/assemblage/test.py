#!/usr/bin/env python2
# -*- coding: UTF-8 -*-


import os
import tempfile

from __init__ import detect_as_c_magic_flags
from ContextDict import ContextDict


def main():
    temp_path = tempfile.gettempdir()
    config_ctx = ContextDict({
        '__temp_path': temp_path
    })
    ninja_path = os.path.join(temp_path, 'build.ninja')
    cc_path = '/usr/bin/cc'
    print detect_as_c_magic_flags(config_ctx, ninja_path, cc_path)

if __name__ == '__main__':
    main()