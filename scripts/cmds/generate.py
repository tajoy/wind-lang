#!/usr/bin/env python2
# -*- coding: UTF-8 -*-

import sys
import os

from . import Command
from assemblage import generate

class GenerateCommand(Command):
    def __init__(self):
        super(GenerateCommand, self).__init__('generate')

    def build_parser(self, parser):
        parser.add_argument(
            '--force-generate',
            action='store_true',
            help='force generate ninja build file, delete if exists',
            dest='force_generate'
        )

        parser.add_argument(
            '--temp-path',
            type=str,
            help='temprory path for compile and build files, include object files, ninja files, output files.',
            dest='temp_path'
        )

        parser.add_argument(
            '--cc-exec',
            type=str,
            help='C compiler executable file name, will find in $PATH or --cross-compile-root',
            dest='cc_exec'
        )
        parser.add_argument(
            '--cpp-exec',
            type=str,
            help='C++ compiler executable file name, will find in $PATH or --cross-compile-root',
            dest='cpp_exec'
        )
        parser.add_argument(
            '--ld-exec',
            type=str,
            help='linker executable file name, will find in $PATH or --cross-compile-root',
            dest='ld_exec'
        )
        parser.add_argument(
            '--cc-path',
            type=str,
            help='C compiler executable full path',
            dest='cc_path'
        )
        parser.add_argument(
            '--cpp-path',
            type=str,
            help='C++ compiler executable full path',
            dest='cpp_path'
        )
        parser.add_argument(
            '--ld-path',
            type=str,
            help='linker executable full path',
            dest='ld_path'
        )
        parser.add_argument(
            '--cross-compile-root',
            type=str,
            help='use for cross compile, root of cross compile toolchain',
            dest='cross_compile_root'
        )
        
        parser.add_argument(
            '--system',
            type=str,
            choices=['darwin', 'linux', 'unix', 'windows'],
            help='use for cross compile, compile target system',
            dest='system'
        )

        parser.add_argument(
            '--os',
            type=str,
            choices=['apple', 'linux', 'windows', 'ios', 'android'],
            help='use for cross compile, compile target os',
            dest='os'
        )

        parser.add_argument(
            '--arch',
            type=str,
            choices=[
                'i386', 'i586', 'i686', 'x86_64',
                'arm', 'armv5te', 'armv7', 'armv7s', 'aarch64',
                'mips', 'mips64', 'mips64el', 'mipsel',
                'powerpc', 'powerpc64', 'powerpc64le',
            ],
            help='use for cross compile, compile target arch',
            dest='arch'
        )

        parser.add_argument(
            '--abi',
            type=str,
            choices=[
                'eabi', 'eabihf',
                'gnu', 'gnux32', 'gnueabi', 'gnueabihf', 'gnuabi64',
                'musl','musleabi', 'musleabihf',
                'androideabi', 
                'msvc', 
                'netbsd',
                'cloudabi',
                'fuchsia',
                'redox',
            ],
            help='use for cross compile, compile target (e)abi',
            dest='abi'
        )

        parser.add_argument(
            '--cc-flags',
            type=str,
            help='C compile flags',
            dest='cc_flags'
        )
        parser.add_argument(
            '--cpp-flags',
            type=str,
            help='C++ compile flags',
            dest='cpp_flags'
        )
        parser.add_argument(
            '--ld-flags',
            type=str,
            help='linker flags',
            dest='ld_flags'
        )

    def execute(self, args):
        options = {}
        for key, value in args.items():
            if value is not None:
                options[key] = value
        generate(options)