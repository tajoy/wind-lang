#!/usr/bin/env python2
# -*- coding: UTF-8 -*-

import sys
import os

from . import Command
from assemblage import clean
from generate import GenerateCommand

class CleanCommand(GenerateCommand):
    def __init__(self):
        Command.__init__(self, 'clean')
    
    def execute(self, args):
        options = {}
        for key, value in args.items():
            if value is not None:
                options[key] = value
        clean(options)