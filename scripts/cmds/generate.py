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
            '--config', '-c',
            type=str,
            help='specify config file',
            dest='__config'
        )

        parser.add_argument(
            '--change-dir', '-C',
            type=str,
            help='change current directory to',
            dest='__change_dir'
        )

        parser.add_argument(
            '--force-generate', '-f',
            action='store_true',
            help='force generate ninja build file, delete if exists',
            dest='__force_generate'
        )

        parser.add_argument(
            '--temp-path', '-T',
            type=str,
            help='temprory path for compile and build files, include object files, ninja files, output files.',
            dest='__temp_path'
        )

        parser.add_argument(
            '--cc-exec',
            type=str,
            help='C compiler executable file name, will find in $PATH or --cross-compile-root',
            dest='__cc_exec'
        )

        parser.add_argument(
            '--cpp-exec',
            type=str,
            help='C++ compiler executable file name, will find in $PATH or --cross-compile-root',
            dest='__cpp_exec'
        )

        parser.add_argument(
            '--ld-exec',
            type=str,
            help='linker executable file name, will find in $PATH or --cross-compile-root',
            dest='__ld_exec'
        )

        parser.add_argument(
            '--cc-path',
            type=str,
            help='C compiler executable full path',
            dest='__cc_path'
        )

        parser.add_argument(
            '--cpp-path',
            type=str,
            help='C++ compiler executable full path',
            dest='__cpp_path'
        )

        parser.add_argument(
            '--ld-path',
            type=str,
            help='linker executable full path',
            dest='__ld_path'
        )

        parser.add_argument(
            '--cross-compile-root', '-X',
            type=str,
            help='use for cross compile, root of cross compile toolchain',
            dest='__cross_compile_root'
        )
        
        parser.add_argument(
            '--system',
            type=str,
            choices=['darwin', 'linux', 'unix', 'windows'],
            help='use for cross compile, compile target system',
            dest='__system'
        )

        parser.add_argument(
            '--os',
            type=str,
            choices=['apple', 'linux', 'windows', 'ios', 'android'],
            help='use for cross compile, compile target os',
            dest='__os'
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
            dest='__arch'
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
            dest='__abi'
        )

        parser.add_argument(
            '--cc-flags',
            type=str,
            help='C compile flags',
            dest='__cc_flags'
        )
        
        parser.add_argument(
            '--cpp-flags',
            type=str,
            help='C++ compile flags',
            dest='__cpp_flags'
        )

        parser.add_argument(
            '--ld-flags',
            type=str,
            help='linker flags',
            dest='__ld_flags'
        )

    def execute(self, args):
        options = {}
        for key, value in args.items():
            if value is not None:
                options[key] = value
        generate(options)