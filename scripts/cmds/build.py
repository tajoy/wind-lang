#!/usr/bin/env python2
# -*- coding: UTF-8 -*-

import sys
import os

from . import Command
from assemblage import build
from generate import GenerateCommand

class BuildCommand(GenerateCommand):
    def __init__(self):
        Command.__init__(self, 'build')

    def execute(self, args):
        options = {}
        for key, value in args.items():
            if value is not None:
                options[key] = value
        build(options)