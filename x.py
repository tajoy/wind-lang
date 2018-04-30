#!/usr/bin/env python2
# -*- coding: UTF-8 -*-

import sys
import os

ROOT_DIR = os.path.dirname(os.path.realpath(__file__))
SCRIPTS_DIR = os.path.join(ROOT_DIR, 'scripts')
sys.path.append(SCRIPTS_DIR)

print SCRIPTS_DIR

from cmds import RootCommand



def main():
    RootCommand().run()

if __name__ == '__main__':
    main()





