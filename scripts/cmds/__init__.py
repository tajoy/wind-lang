#!/usr/bin/env python2
# -*- coding: UTF-8 -*-




from argparse import ArgumentParser

import abc

class Command(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self, name, *args, **kvargs):
        self.name = name
        self.args = args
        self.kvargs = kvargs
        self.parent_command = None
        self.sub_command = None
        self.sub_commands = {}
    
    def add_subcommand(self, command):
        if not isinstance(command, Command):
            raise TypeError('can not add an instance that is not Command!')
        command.parent_command = self
        self.sub_commands[command.name] = command

    @abc.abstractmethod
    def build_parser(self, parser):
        pass

    def parse_args(self):
        parser = ArgumentParser(*self.args, **self.kvargs)
        self.build_parser(parser)
        subparsers = parser.add_subparsers(title='sub-commands')
        for name, command in self.sub_commands.items():
            subparser = subparsers.add_parser(command.name, *command.args, **command.kvargs)
            command.build_parser(subparser)
            subparser.set_defaults(sub_command=name)
        ret = vars(parser.parse_args())
        self.sub_command = ret.pop('sub_command', None)
        return self.sub_command, ret
    
    def run(self):
        sub_command, args = self.parse_args()
        if sub_command is not None and sub_command in self.sub_commands:
            command = self.sub_commands[sub_command]
            command.execute(args)
        else:
            self.execute(args)

    def execute(self, args):
        raise NotImplementedError



from build import BuildCommand
from generate import GenerateCommand
from clean import CleanCommand
class RootCommand(Command):
    def __init__(self):
        super(RootCommand, self).__init__('root')
        self.add_subcommand(GenerateCommand())
        self.add_subcommand(BuildCommand())
        self.add_subcommand(CleanCommand())

    def build_parser(self, parser):
        pass

    def execute(self, args):
        pass