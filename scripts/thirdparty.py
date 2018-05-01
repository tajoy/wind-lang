#!/usr/bin/env python2
# -*- coding: UTF-8 -*-
import os

try:
    import preconditions
except ImportError:
    os.system('pip install preconditions')

try:
    import toml
except ImportError:
    os.system('pip install toml')

try:
    import ninja
except ImportError:
    os.system('pip install ninja')