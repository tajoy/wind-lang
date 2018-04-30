#!/bin/env python2
# -*- coding: UTF-8 -*-




from argparse import ArgumentParser

class Command(object):
    def __init__(self, name, *args, **kvargs):
        self.name = name
        self.args = args
        self.kvargs = kvargs
        self.sub_command = None
        self.sub_commands = {}
    
    def add_subcommand(self, command):
        if not isinstance(command, Command):
            raise TypeError('can not add an instance that is not Command!')
        self.sub_commands[command.name] = command

    def build_parser(self, parser):
        pass

    def parse_args(self):
        parser = ArgumentParser(*self.args, **self.kvargs)
        self.build_parser(parser)
        subparsers = parser.add_subparsers(title='sub-commands')
        for (name, command) in self.sub_commands:
            subparser = subparsers.add_parser(*command.args, **command.kvargs)
            command.build_parser(subparser)
            def __set_name(args):
                self.sub_command = name
            subparser.set_defaults(func=__set_name)
        self.sub_command = None
        ret = parser.parse_args()
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
class RootCommand(Command):
    def __init__(self):
        super(RootCommand, self).__init__('root')
        self.add_subcommand(BuildCommand())

    def build_parser(self, parser):
        pass

    def execute(self, args):
        pass