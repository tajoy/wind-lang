#!/usr/bin/env python2
# -*- coding: UTF-8 -*-


import os
import sys
import re

import preconditions
import toml
import ninja
import platform

from ContextDict import ContextDict

RE_PATTERN_TYPE = None
if hasattr(re, '_pattern_type'):
    RE_PATTERN_TYPE = re._pattern_type
else:
    RE_PATTERN_TYPE = type(re.compile(''))


def calc_temp_path(config_ctx, path):
    temp_path = config_ctx.getOrDefault('temp_path', os.path.join(os.path.curdir, 'build'))
    cwd = os.path.realpath(os.path.curdir)
    temp_path = os.path.realpath(temp_path)
    path = os.path.realpath(path)
    if path.startswith(cwd):
        retpath = os.path.join(temp_path, path.replace(cwd, ''))
    else:
        retpath = os.path.join(temp_path, path)
    ensure_dir(os.path.dirname(retpath))
    return retpath

def ensure_dir(path):
    if not os.path.isdir(path):
        os.makedirs(path)

def exists_executable(path):
    return os.path.isfile(path) and os.access(path, os.X_OK)

def find_exec_path(exec_name, paths):
    for path in paths:
        exec_path = os.path.join(path, exec_name)
        if exists_executable(exec_path):
            return exec_path
    raise IOError('can not found executable:' + exec_name)

def get_rel_path(config_ctx, ninja_path, rel_path):
    full_path = None
    if not rel_path.startswith('/'):
        temp_path = os.path.join(os.path.curdir, rel_path)
        if full_path is None and os.path.exists(temp_path):
            full_path = temp_path
        
        if '___include_toml_path' in config_ctx:
            temp_path = os.path.join(config_ctx['___include_toml_path'], rel_path)
            if full_path is None and os.path.exists(temp_path):
                full_path = temp_path
        
        temp_path = os.path.join(os.path.dirname(ninja_path), rel_path)
        if full_path is None and os.path.exists(temp_path):
            full_path = temp_path
    else:
        full_path = rel_path
    return full_path


def embed_ninja(config_ctx, ninja_path, ninja_writer):
    cc_exec = config_ctx.get('cc_exec', 'cc')
    cpp_exec = config_ctx.get('cpp_exec', 'cpp')
    ld_exec = config_ctx.get('ld_exec', 'ld')
    cc_path = config_ctx.get('cc_path', None)
    cpp_path = config_ctx.get('cpp_path', None)
    ld_path = config_ctx.get('ld_path', None)
    cross_compile_root = config_ctx.get('cross_compile_root', None)
    bin_paths = os.environ['PATH'].split(os.path.pathsep)
    if cross_compile_root is not None:
        bin_paths = [
            cross_compile_root,
            os.path.join(cross_compile_root, 'bin'),
            os.path.join(cross_compile_root, 'sbin'),
            os.path.join(cross_compile_root, 'local', 'bin'),
            os.path.join(cross_compile_root, 'local', 'sbin'),
            os.path.join(cross_compile_root, 'user', 'bin'),
            os.path.join(cross_compile_root, 'user', 'sbin'),
            os.path.join(cross_compile_root, 'user', 'local', 'bin'),
            os.path.join(cross_compile_root, 'user', 'local', 'sbin'),
        ]
    if cc_path is None:
        cc_path = find_exec_path(cc_exec, bin_paths)
    if cpp_path is None:
        cpp_path = find_exec_path(cpp_exec, bin_paths)
    if ld_path is None:
        ld_path = find_exec_path(ld_exec, bin_paths)

    if not exists_executable(cc_path):
        raise IOError('executable file not exists or can not execute:' + cc_exec)
    if not exists_executable(cpp_path):
        raise IOError('executable file not exists or can not execute:' + cpp_exec)
    if not exists_executable(ld_path):
        raise IOError('executable file not exists or can not execute:' + ld_exec)

    cc_flags = config_ctx.get('cc_flags', '')
    cpp_flags = config_ctx.get('cpp_flags', '')
    ld_flags = config_ctx.get('ld_flags', '')

    ninja_writer.pool('__link_pool', 1)

    ninja_writer.rule(
        '__cc',
        '"%s" %s $__cc_flags -MMD -MT $out -MF $out.d -c $in -o $out' % (cc_path, cc_flags),
        description='compile(c) $out',
        depfile='$out.d',
        deps='gcc'
    )

    ninja_writer.rule(
        '__cpp',
        '"%s" %s $__cpp_flags -MMD -MT $out -MF $out.d -c $in -o $out' % (cpp_path, cpp_flags),
        description='compile(cpp) $out',
        depfile='$out.d',
        deps='gcc'
    )

    ninja_writer.rule(
        '__ld',
        '"%s" %s $__ld_flags -o $out $in' % (ld_path, ld_flags),
        description='link($__link_type) $out',
        pool='__link_pool'
    )

def write_target_ninja(config_ctx, ninja_path, ninja_writer, target):
    target = dict(target)
    conditions = config_ctx.format(target.pop('conditions', []))
    for condition in conditions:
        cond = target.pop('condition')
        # TODO: change properties when cross compiling
        __locals__ = {
            'OS': platform.system(),
            'architecture': platform.architecture(),
            'release': platform.release(),
            'machine': platform.machine(),
            'processor': platform.processor(),
            'uname': platform.uname(),
            'version': platform.version(),
        }
        if hasattr(platform, 'mac_ver'):
            __locals__['mac_ver'] = platform.mac_ver()
        if hasattr(platform, 'win32_ver'):
            __locals__['win32_ver'] = platform.win32_ver()
        if hasattr(platform, 'linux_distribution'):
            __locals__['linux_distribution'] = platform.linux_distribution()
        if eval(cond, __locals__) is True:
            target.update(condition)

    name = config_ctx.format(target.pop('name'))
    type_name = config_ctx.format(target.pop('type'))
    sources = config_ctx.format(target.pop('sources'))
    include_dirs = [config_ctx.format(dirpath) for dirpath in target.pop('include_dirs', [])]
    defines = config_ctx.format(target.pop('defines', []))
    cflags = config_ctx.format(target.pop('cflags', ''))
    cppflags = config_ctx.format(target.pop('cppflags', ''))
    ldflags = config_ctx.format(target.pop('ldflags', ''))
    rule_map = {
        '__cc': re.compile(r'.*(\.cc|.c)'),
        '__cpp': re.compile(r'.*(\.cpp|.c\+\+)'),
    }
    rule_map.update(target.pop('rule_map', {}))
    keys = rule_map.keys()
    for key in keys:
        value = rule_map[key]
        if isinstance(value, (str, unicode, )) and not isinstance(value, RE_PATTERN_TYPE):
            rule_map[key] = re.compile(value)


    for include_dir in include_dirs:
        full_path = get_rel_path(config_ctx, ninja_path, include_dir) or include_dir
        cflags += ' -I "%s"' % (full_path)
        cppflags += ' -I "%s"' % (full_path)

    for define in defines:
        cflags += ' -D %s' % (define)
        cppflags += ' -D %s' % (define)

    source_paths = []
    object_paths = []
    for source in sources:
        source_path = get_rel_path(config_ctx, ninja_path, source) or source
        source_paths.append(source_path)
        object_path = calc_temp_path(config_ctx, source_path + '.o')
        object_paths.append(object_path)
        build_rule = None
        for rule, pattern in rule_map.items():
            if pattern.match(source_path):
                build_rule = rule
                break
        if build_rule is None:
            raise StandardError('Can not map rule for source: ' + source_path)
        flags = ''
        if build_rule == '__cc':
            flags = cflags
        if build_rule == '__cpp':
            flags = cppflags
        ninja_writer.build(
            object_path, build_rule,
            inputs=source_path,
            variables={
                build_rule + '_flags': flags,
            },
        )
    output_path = name
    if type_name == 'executable':
        ninja_writer.build(
            output_path, '__ld',
            inputs=' '.join(object_paths),
            variables={
                '__ld_flags': ldflags,
            },
        )
    elif type_name == 'dynamic_library':
        ninja_writer.build(
            output_path, '__ld',
            inputs=' '.join(object_paths),
            variables={
                '__ld_flags': ldflags,
            },
        )
    elif type_name == 'static_library':
        ninja_writer.build(
            output_path, '__ld',
            inputs=' '.join(object_paths),
            variables={
                '__ld_flags': ldflags,
            },
        )
    else:
        raise StandardError('unknown target type: ' + type_name)


def write_ninja(config_ctx, ninja_path, ninja_writer):
    keys = config_ctx.keys()
    for key in keys:
        value = config_ctx[key]
        if key == 'build' and isinstance(value, dict):
            value = ContextDict(value)
            outputs = value.pop('outputs')
            rule = value.pop('rule', None)
            inputs = value.pop('inputs', None)
            implicit = value.pop('implicit', None)
            order_only = value.pop('order_only', None)
            implicit_outputs = value.pop('implicit_outputs', None)
            variables={}
            for key in value.keys():
                variables[key] = value.get(key)
            ninja_writer.build(
                outputs, rule,
                inputs=inputs,
                implicit=implicit,
                order_only=order_only,
                implicit_outputs=implicit_outputs,
                variables=variables
            )
        elif key == 'default':
            if isinstance(value, list):
                items = []
                for item in value:
                    if isinstance(item, (str, unicode,)):
                        items.append(item)
                ninja_writer.default(items)
            if isinstance(value, (str, unicode,)):
                ninja_writer.default([value, ])
        elif key == 'include' or key == 'subninja':
            if not isinstance(value, (str, unicode,)):
                continue
            sub_path = value
            if not sub_path.startswith('/'):
                sub_path = get_rel_path(config_ctx, ninja_path, sub_path)
            if sub_path is None or not os.path.isfile(sub_path):
                raise IOError(key + ' file not found:' + value)
            if value.endswith('.ninja'):
                if key == 'include':
                    ninja_writer.include(sub_path)
                if key == 'subninja':
                    ninja_writer.subninja(sub_path)
                
            if value.endswith('.toml'):
                new_ctx = config_ctx.clone().merge({
                    '___include_toml_path': sub_path
                })
                sub_path = calc_temp_path(config_ctx, sub_path)
                generate_ninja(new_ctx, sub_path, is_embed=False)
                if key == 'include':
                    ninja_writer.include(sub_path)
                if key == 'subninja':
                    ninja_writer.subninja(sub_path)
        elif key == 'pool' and isinstance(value, dict):
            value = ContextDict(value)
            name = value.pop('name')
            depth = value.pop('depth', 1)
            ninja_writer.pool(name, depth)
        elif key == 'rule' and isinstance(value, dict):
            value = ContextDict(value)
            name = value.pop('name')
            command = value.pop('command')
            description = value.pop('description', None)
            depfile = value.pop('depfile', None)
            generator = value.pop('generator', False)
            pool = value.pop('pool', None)
            restat = value.pop('restat', False)
            rspfile = value.pop('rspfile', None)
            rspfile_content = value.pop('rspfile_content', None)
            deps = value.pop('deps', None)
            ninja_writer.rule(
                name, command,
                description=description,
                depfile=depfile,
                generator=generator,
                pool=pool,
                restat=restat,
                rspfile=rspfile,
                rspfile_content=rspfile_content,
                deps=deps
            )
        # custom key
        elif key == 'targets' and isinstance(value, list):
            for target in value:
                write_target_ninja(config_ctx, ninja_path, ninja_writer, target)
        # others is variable
        else:
            if isinstance(value, (dict, list, )):
                continue
            if isinstance(value, (str, unicode, )):
                if value.startswith('__'):
                    continue
            ninja_writer.variable(key, value)

def generate_ninja(config_ctx, ninja_path, is_embed=True):
    if os.path.exists(ninja_path):
        os.remove(ninja_path)
    ensure_dir(os.path.dirname(ninja_path))
    with open(ninja_path, 'w') as ninja_file:
        ninja_writer = ninja.ninja_syntax.Writer(ninja_file)
        if is_embed:
            embed_ninja(config_ctx, ninja_path, ninja_writer)
        write_ninja(config_ctx, ninja_path, ninja_writer)

def ensure_ninja(config_ctx, ninja_path):
    pass

def build_ninja(config_ctx, ninja_path):
    pass

def clean_ninja(config_ctx, ninja_path):
    pass

def config_context(options):
    if 'change_dir' in options:
        os.chdir(options['change_dir'])
    config_file = options.get('config', os.path.join(os.path.curdir, 'build.toml'))
    if not os.path.isfile(config_file):
        raise IOError("config file not found: " + config_file)
    config = {}
    with open(config_file, 'r') as conf_file:
        config = toml.loads(conf_file.read())
    config_ctx = ContextDict(config)
    config_ctx.update(options)
    return config_ctx

def generate(options, config_ctx=None):
    if config_ctx is None:
        config_ctx = config_context(options)
    temp_path = config_ctx.getOrDefault('temp_path', os.path.join(os.path.curdir, 'build'))
    ensure_dir(temp_path)
    ninja_path = os.path.join(temp_path, 'build.ninja')
    is_force = config_ctx.getOrDefault('force_generate', False)
    if is_force:
         generate_ninja(config_ctx, ninja_path)
    else:
         ensure_ninja(config_ctx, ninja_path)
    return ninja_path

def build(options, config_ctx=None):
    if config_ctx is None:
        config_ctx = config_context(options)
    ninja_path = generate(options, config_ctx=config_ctx)
    build_ninja(config_ctx, ninja_path)

def clean(options, config_ctx=None):
    if config_ctx is None:
        config_ctx = config_context(options)
    ninja_path = generate(options, config_ctx=config_ctx)
    clean_ninja(config_ctx, ninja_path)
    os.remove(ninja_path)
