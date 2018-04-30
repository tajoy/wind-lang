#!/usr/bin/env python2
# -*- coding: UTF-8 -*-


import sys
import os

from argparse import ArgumentParser


try:
    import toml
except ImportError:
    os.system('pip install toml')
    import toml

from . import Command


class BuildCommand(Command):
    def __init__(self):
        super(BuildCommand, self).__init__('build')

    def build_parser(self, parser):
        parser.add_argument('--c-flags', type=str)
        parser.add_argument('--ld-flags', type=str)

    def execute(self, args):
        pass