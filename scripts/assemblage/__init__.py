#!/usr/bin/env python2
# -*- coding: UTF-8 -*-


import os
import sys
import re
import subprocess
import multiprocessing
import platform
import glob
import shlex
import shutil

import preconditions
import toml
import ninja

from ContextDict import ContextDict

RE_PATTERN_TYPE = None
if hasattr(re, '_pattern_type'):
    RE_PATTERN_TYPE = re._pattern_type
else:
    RE_PATTERN_TYPE = type(re.compile(''))

REGISTERED_LIBRARY_PLUGINS = {}


__all__ = [
    'build',
    'generate',
    'clean',
]

def as_list(obj):
    if isinstance(obj, list):
        return obj
    return [obj]

def calc_temp_path(config_ctx, path):
    temp_path = config_ctx.getOrDefault('__temp_path', os.path.join(os.path.curdir, 'build'))
    cwd = os.path.realpath(os.path.curdir)
    temp_path = os.path.realpath(temp_path)
    if path.startswith(cwd):
        retpath = os.path.join(temp_path, path.replace(os.path.join(cwd, ''), ''))
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


def glob_in_path(curdir, glob_path):
    before_dir = os.path.realpath(os.curdir)
    os.chdir(curdir)
    ret = glob.glob(glob_path)
    os.chdir(before_dir)
    return ret

def full_real_path(curdir, rel_path):
    before_dir = os.path.realpath(os.curdir)
    os.chdir(curdir)
    ret = os.path.abspath(os.path.realpath(rel_path))
    os.chdir(before_dir)
    return ret

def get_rel_path(config_ctx, ninja_path, rel_path):
    full_path = None
    if not rel_path.startswith('/'):
        if '___include_toml_path' in config_ctx:
            toml_dir = os.path.dirname(config_ctx['___include_toml_path'])
            temp_path = os.path.join(toml_dir, rel_path)
            if full_path is None and os.path.exists(temp_path):
                full_path = temp_path
        
        temp_path = os.path.join(os.path.curdir, rel_path)
        if full_path is None and os.path.exists(temp_path):
            full_path = temp_path
        
        temp_path = os.path.join(os.path.dirname(ninja_path), rel_path)
        if full_path is None and os.path.exists(temp_path):
            full_path = temp_path
    else:
        full_path = rel_path
    return full_path

def get_rel_glob_path(config_ctx, ninja_path, glob_path):
    paths = []
    if not glob_path.startswith('/'):
        if '___include_toml_path' in config_ctx:
            toml_dir = os.path.dirname(config_ctx['___include_toml_path'])
            temp_path = glob_in_path(toml_dir, glob_path)
            if len(temp_path) > 0:
                paths += [full_real_path(toml_dir, p) for p in temp_path]
        
        if len(paths) <= 0:
            temp_path = glob_in_path(os.curdir, glob_path)
            if len(temp_path) > 0:
                paths += [full_real_path(toml_dir, p) for p in temp_path]
        
        if len(paths) <= 0:
            ninja_dir = os.path.dirname(ninja_path)
            temp_path = glob_in_path(ninja_dir, glob_path)
            if len(temp_path) > 0:
                paths += [full_real_path(toml_dir, p) for p in temp_path]
    else:
        paths = glob.glob(glob_path)
    return paths

def run_cmd(prog, args):
    cmd = subprocess.Popen(
        [prog] + args, 
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT
    )
    cmd.wait()
    return cmd.stdout.read()


def detect_sequence_in_lines_args(lines_args, sequence):
    len_sequence = len(sequence)
    for i in xrange(0, len(lines_args)):
        args = lines_args[i]
        for i in xrange(0, len(args) - len_sequence):
            if args[i : i + len_sequence] == sequence:
                return args[:i] + args[i + len_sequence:]
    return None

def strip_lines_args(lines_args1, lines_args2):
    if len(lines_args1) > len(lines_args2):
        lines_args2, lines_args1 = lines_args1, lines_args2
    lines_args = []
    for i in xrange(0, len(lines_args1)):
        args = []
        args1 = lines_args1[i]
        args2 = lines_args2[i]
        if len(args1) > 0 and args1[0].find('=') >= 0:
            args1 = args1[0].split('=')[1:] + args1[1:]
        if len(args2) > 0 and args2[0].find('=') >= 0:
            args2 = args2[0].split('=')[-1:] + args2[1:]
        if len(args1) > len(args2):
            args2, args1 = args1, args2
        for j in xrange(0, len(args1)):
            arg1 = args1[j]
            arg2 = args2[j]
            if arg1 == arg2:
                args.append(arg1)
        lines_args.append(args)
    return lines_args

def detect_ld_magic_flags(config_ctx, ninja_path, cc_path):
    pass

def detect_as_c_magic_flags(config_ctx, ninja_path, cc_path):
    hello1_path = calc_temp_path(config_ctx, os.path.join('__detect', 'hello.c'))
    out1_path = calc_temp_path(config_ctx, os.path.join('__detect', 'hello.s'))
    hello2_path = calc_temp_path(config_ctx, os.path.join('__detect', 'hello2', 'hello2.c'))
    out2_path = calc_temp_path(config_ctx, os.path.join('__detect', 'hello2', 'hello2.s'))
    if os.path.exists(hello1_path):
        os.remove(hello1_path)
    ensure_dir(os.path.dirname(hello1_path))
    with open(hello1_path, 'w') as hello_file:
        hello_file.write(
"""
#include <stdio.h>
#include <stdlib.h>
int main(int argc, char** args) {
    return 0;
}
""")
    ensure_dir(os.path.dirname(hello2_path))
    shutil.copyfile(hello1_path, hello2_path)
    output1 = run_cmd(cc_path, ['-S', hello1_path, '-o', out1_path, '-###'])
    lines_args1 = [shlex.split(line) for line in output1.splitlines()]
    output2 = run_cmd(cc_path, ['-S', hello2_path, '-o', out2_path, '-###'])
    lines_args2 = [shlex.split(line) for line in output2.splitlines()]
    lines_args = strip_lines_args(lines_args1, lines_args2)
    args = detect_sequence_in_lines_args(lines_args, ['-S', hello1_path, '-o', out1_path])
    if args is not None:
        return args
    args = detect_sequence_in_lines_args(lines_args, ['-S', hello2_path, '-o', out2_path])
    if args is not None:
        return args
    return ''

def detect_as_cpp_magic_flags(config_ctx, ninja_path, cpp_path):
    hello1_path = calc_temp_path(config_ctx, os.path.join('__detect', 'hello.cpp'))
    out1_path = calc_temp_path(config_ctx, os.path.join('__detect', 'hello.s'))
    hello2_path = calc_temp_path(config_ctx, os.path.join('__detect', 'hello2', 'hello2.cpp'))
    out2_path = calc_temp_path(config_ctx, os.path.join('__detect', 'hello2', 'hello2.s'))
    if os.path.exists(hello1_path):
        os.remove(hello1_path)
    ensure_dir(os.path.dirname(hello1_path))
    with open(hello1_path, 'w') as hello_file:
        hello_file.write(
"""
#include <iostream>
#include <stdio.h>
#include <stdlib.h>
int main(int argc, char** args) {
    return 0;
}
""")
    ensure_dir(os.path.dirname(hello2_path))
    shutil.copyfile(hello1_path, hello2_path)

    output1 = run_cmd(cpp_path, ['-S', hello1_path, '-o', out1_path, '-###'])
    lines_args1 = [shlex.split(line) for line in output1.splitlines()]
    output2 = run_cmd(cpp_path, ['-S', hello2_path, '-o', out2_path, '-###'])
    lines_args2 = [shlex.split(line) for line in output2.splitlines()]

def detect_object_magic_flags(config_ctx, ninja_path, cc_path, c_file):
    pass
    

def embed_ninja(config_ctx, ninja_path, ninja_writer):
    cc_exec = config_ctx.get('__cc_exec', 'cc')
    cpp_exec = config_ctx.get('__cpp_exec', 'cpp')
    ld_exec = config_ctx.get('__ld_exec', 'ld')
    as_exec = config_ctx.get('__as_exec', 'as')
    cc_path = config_ctx.get('__cc_path', None)
    cpp_path = config_ctx.get('__cpp_path', None)
    ld_path = config_ctx.get('__ld_path', None)
    as_path = config_ctx.get('__as_path', None)
    cross_compile_root = config_ctx.get('__cross_compile_root', None)
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
    if as_path is None:
        as_path = find_exec_path(as_exec, bin_paths)

    if not exists_executable(cc_path):
        raise IOError('executable file not exists or can not execute:' + cc_exec)
    if not exists_executable(cpp_path):
        raise IOError('executable file not exists or can not execute:' + cpp_exec)
    if not exists_executable(ld_path):
        raise IOError('executable file not exists or can not execute:' + ld_exec)
    if not exists_executable(as_path):
        raise IOError('executable file not exists or can not execute:' + as_exec)

    cc_flags = config_ctx.get('__cc_flags', '')
    cpp_flags = config_ctx.get('__cpp_flags', '')
    ld_flags = config_ctx.get('__ld_flags', '')
    as_c_flags = config_ctx.get('__as_c_flags', '')
    as_cpp_flags = config_ctx.get('__as_cpp_flags', '')

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
        description='link $out',
        pool='__link_pool'
    )

    ninja_writer.rule(
        '__as_c',
        '"%s" %s $__as_c_flags -o $out $in' % (as_path, as_c_flags),
        description='assemble C $out'
    )

    ninja_writer.rule(
        '__as_cpp',
        '"%s" %s $__as_cpp_flags -o $out $in' % (as_path, as_cpp_flags),
        description='assemble C++ $out'
    )


def write_build_ninja(config_ctx, ninja_path, ninja_writer, data):
    build_dict = ContextDict(data)
    outputs = build_dict.pop('outputs')
    rule = build_dict.pop('rule', None)
    inputs = build_dict.pop('inputs', None)
    implicit = build_dict.pop('implicit', None)
    order_only = build_dict.pop('order_only', None)
    implicit_outputs = build_dict.pop('implicit_outputs', None)
    variables={}
    for key in build_dict.keys():
        variables[key] = build_dict.get(key)
    ninja_writer.build(
        outputs, rule,
        inputs=inputs,
        implicit=implicit,
        order_only=order_only,
        implicit_outputs=implicit_outputs,
        variables=variables
    )
def write_pool_ninja(config_ctx, ninja_path, ninja_writer, data):
    pool = ContextDict(data)
    name = pool.pop('name')
    depth = pool.pop('depth', 1)
    ninja_writer.pool(name, depth)

def write_rule_ninja(config_ctx, ninja_path, ninja_writer, data):
    rule = ContextDict(data)
    name = rule.pop('name')
    command = rule.pop('command')
    description = rule.pop('description', None)
    depfile = rule.pop('depfile', None)
    generator = rule.pop('generator', False)
    pool = rule.pop('pool', None)
    restat = rule.pop('restat', False)
    rspfile = rule.pop('rspfile', None)
    rspfile_content = rule.pop('rspfile_content', None)
    deps = rule.pop('deps', None)
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

def write_include_ninja(config_ctx, ninja_path, ninja_writer, data):
    sub_path = None
    if not data.startswith('/'):
        if not data.endswith('.toml') and not data.endswith('.ninja'):
            sub_path = get_rel_path(config_ctx, ninja_path, data + '.toml')
            if sub_path is None:
                sub_path = get_rel_path(config_ctx, ninja_path, data + '.ninja')
        else:
            sub_path = get_rel_path(config_ctx, ninja_path, data)
    else:
        if not data.endswith('.toml') and not data.endswith('.ninja'):
            sub_path = data + '.toml'
    if sub_path is None or not os.path.isfile(sub_path):
        raise IOError('include file not found:' + data)

    if sub_path.endswith('.ninja'):
        ninja_writer.include(sub_path)
    if sub_path.endswith('.toml'):
        config = {}
        with open(sub_path, 'r') as conf_file:
            config = toml.loads(conf_file.read())
        new_ctx = ContextDict(config)
        new_ctx = new_ctx.merge({
            '___include_toml_path': sub_path
        })
        write_ninja(new_ctx, ninja_path, ninja_writer)
        # new_ninja_path = sub_path[] + '.ninja'
        # sub_path = calc_temp_path(config_ctx, sub_path)
        # generate_ninja(new_ctx, sub_path, is_embed=False)
        # ninja_writer.include(sub_path)

def write_subninja_ninja(config_ctx, ninja_path, ninja_writer, data):
    sub_path = None
    if not data.startswith('/'):
        if data.endswith('.ninja'):
            sub_path = get_rel_path(config_ctx, ninja_path, data)
        else:
            sub_path = get_rel_path(config_ctx, ninja_path, data + '.ninja')
    else:
        if not data.endswith('.ninja'):
            sub_path = data + '.ninja'
    if sub_path is None or not os.path.isfile(sub_path):
        raise IOError('subninja file not found:' + data)
    ninja_writer.subninja(sub_path)

def register_library_plugin(plugin_name, plugin_or_path):
    global REGISTERED_LIBRARY_PLUGINS
    if plugin_name in REGISTERED_LIBRARY_PLUGINS:
        fn = REGISTERED_LIBRARY_PLUGINS[plugin_name]
        raise StandardError(
            'plugin "%s":"%s" plugin name is conflicted with "%s"!' % (
                plugin_name, plugin_or_path, fn.__code__.co_filename
            )
        )
    if callable(plugin_or_path):
        fn = plugin_or_path
        plugin_path = fn.__code__.co_filename
    else:
        g = {}
        execfile(plugin_path, g)
        if 'find' not in g:
            raise StandardError(
                'plugin "%s":"%s" expect "find" function, but not found!' % (
                    plugin_name, plugin_path
                )
            )
        fn = g['find']
    if not callable(fn):
        raise StandardError(
            'plugin "%s":"%s" expect "find" function, but "find" is not function!' % (
                plugin_name, plugin_path
            )
        )
    REGISTERED_LIBRARY_PLUGINS[plugin_name] = fn

def find_dependency_by_plugin(config_ctx, ninja_path, plugin_name, plugin_param):
    global REGISTERED_LIBRARY_PLUGINS
    plugin_deps = None
    plugin_flags = None
    plugin_ldflags = None
    error = None

    if not plugin_name in REGISTERED_LIBRARY_PLUGINS:
        error = StandardError('plugin "%s" not found' % (plugin_name))
        return plugin_deps, plugin_flags, plugin_ldflags, error

    fn = REGISTERED_LIBRARY_PLUGINS[plugin_name]
    try:
        plugin_deps, plugin_flags, plugin_ldflags = fn(plugin_param)
    except Exception as e:
        error = e
    return plugin_deps, plugin_flags, plugin_ldflags, error
    
def find_dependencies(config_ctx, ninja_path, dependencies):
    SYSTEM = config_ctx.get('__system', platform.system()).lower()
    DEFAULT_OS = platform.system()
    if DEFAULT_OS == 'Darwin':
        DEFAULT_OS = 'apple'
    OS = config_ctx.get('__os', DEFAULT_OS).lower()
    ARCH = config_ctx.get('__arch', platform.machine()).lower()
    ABI = config_ctx.get('__abi', 'unknown').lower()

    target_map = config_ctx['__target_map']
    deps = []
    flags = ''
    ldflags = ''
    dependency_target = None
    re_plugin = re.compile(r'^@plugin:([^/]*)//(.*)')
    for dependency in dependencies:
        match_obj = re_plugin.match(dependency)
        if match_obj:
            plugin_name = match_obj.group(1)
            plugin_param = match_obj.group(2)
            plugin_deps, plugin_flags, plugin_ldflags, error = find_dependency_by_plugin(config_ctx, ninja_path, plugin_name, plugin_param)
            if plugin_deps is None or plugin_ldflags is None:
                raise StandardError(
                    'plugin "%s" can not find out dependency by "%s": \n%s' % (
                            plugin_name, plugin_param, str(error)
                        )
                    )
            deps += as_list(plugin_deps)
            flags += plugin_flags
            ldflags += plugin_ldflags
            continue
        
        dep_paths = get_rel_glob_path(config_ctx, ninja_path, dependency)
        if len(dep_paths) > 0:
            for dep_path in dep_paths:
                dep_dir = os.path.dirname(dep_path)
                dep_include_dir = os.path.join(dep_dir, 'include')
                if os.path.isdir(dep_include_dir):
                    flags += ' -I"%s"' % (dep_include_dir)
                dep_include_dir = os.path.join(dep_dir, '..', 'include')
                if os.path.isdir(dep_include_dir):
                    flags += ' -I"%s"' % (dep_include_dir)
                if dep_path.endswith('.so') or dep_path.endswith('.dll'):
                    dep_dir = os.path.dirname(dep_path)
                    ldflags += ' -L"%s"' % (dep_dir)
                    dep_basename = os.path.basename(dep_path)
                    if dep_basename.endswith('.so'):
                        dep_basename = dep_basename[:-3]
                        if dep_basename.startswith('lib'):
                            dep_basename = dep_basename[3:]
                    if dep_basename.endswith('.dll'):
                        dep_basename = dep_basename[:-4]
                    ldflags += ' -l"%s"' % (os.path.basename(dep_basename))
                    ldflags += ' -rpath"%s"' % (dep_dir)
                if dep_path.endswith('.a'):
                    ldflags += ' -L"%s"' % (os.path.dirname(dep_path))
                    dep_basename = os.path.basename(dep_path)
                    if dep_basename.startswith('lib'):
                        dep_basename = dep_basename[3:]
                    ldflags += ' -l"%s"' % (dep_basename)
            continue

        if dependency in target_map:
            dependency_target = target_map[dependency]
        if dependency.startswith('lib'):
            dependency = dependency[3:]
        if dependency in target_map:
            dependency_target = target_map[dependency]
        if dependency.endswith('.a'):
            dependency = dependency[:-2]
        if dependency in target_map:
            dependency_target = target_map[dependency]
        if dependency_target is None:
            raise StandardError('can not dependency on a executable: ' + dependency)
        dependency_name = dependency_target['name']
        dependency_type = dependency_target['type']
        if 'include_dirs' in dependency_target:
            dep_include_dirs = dependency_target['include_dirs']
            for include_dir in dep_include_dirs:
                full_path = get_rel_path(config_ctx, ninja_path, include_dir) or include_dir
                flags += ' -I "%s"' % (full_path)
        if dependency_type == 'executable':
            raise StandardError('can not dependency on a executable: ' + dependency)
        elif dependency_type == 'dynamic_library':
            deps += [dependency_name]
            dependency_path = calc_temp_path(config_ctx, os.path.join('lib', dependency_name))
            if OS == 'windows':
                if not dependency_path.endswith('.dll'):
                    dependency_path += '.dll'
            else:
                if not dependency_path.endswith('.so'):
                    dependency_path += '.so'
            ldflags += ' -L"%s"' % (os.path.dirname(dependency_path))
            dep_basename = os.path.basename(dependency_path)
            if dep_basename.startswith('lib'):
                dep_basename = dep_basename[3:]
            if dep_basename.endswith('.so'):
                dep_basename = dep_basename[:-3]
            if dep_basename.endswith('.dll'):
                dep_basename = dep_basename[:-4]
            ldflags += ' -l"%s"' % (os.path.basename(dep_basename))
            ldflags += ' -rpath"%s"' % (os.path.dirname(dependency_path))
        elif dependency_type == 'static_library':
            deps += [dependency_name]
            dependency_path = calc_temp_path(config_ctx, os.path.join('lib', dependency_name))
            if not dependency_path.endswith('.a'):
                dependency_path += '.a'
            ldflags += ' -L"%s"' % (os.path.dirname(dependency_path))
            dep_basename = os.path.basename(dependency_path)
            if dep_basename.startswith('lib'):
                dep_basename = dep_basename[3:]
            ldflags += ' -l"%s"' % (dep_basename)
        else:
            raise StandardError('unknown target type: ' + dependency_type)

    return deps, flags, ldflags

def write_target_ninja(config_ctx, ninja_path, ninja_writer, data):
    target = dict(data)
    conditions = [config_ctx.format(i) for i in target.pop('conditions', [])]

    SYSTEM = config_ctx.get('__system', platform.system()).lower()
    DEFAULT_OS = platform.system()
    if DEFAULT_OS == 'Darwin':
        DEFAULT_OS = 'apple'
    OS = config_ctx.get('__os', DEFAULT_OS).lower()
    ARCH = config_ctx.get('__arch', platform.machine()).lower()
    ABI = config_ctx.get('__abi', 'unknown').lower()

    for condition in conditions:
        cond = target.pop('condition')
        __locals__ = {
            'SYSTEM': SYSTEM,
            'OS': OS,
            'ARCH': ARCH,
            'ABI': ABI,
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
    sources = [config_ctx.format(i) for i in target.pop('sources', [])]
    dependencies = [config_ctx.format(i) for i in target.pop('dependencies', [])]
    include_dirs = [config_ctx.format(i) for i in target.pop('include_dirs', [])]
    defines = [config_ctx.format(i) for i in target.pop('defines', [])]
    cflags = config_ctx.format(target.pop('cflags', ''))
    cppflags = config_ctx.format(target.pop('cppflags', ''))
    ldflags = config_ctx.format(target.pop('ldflags', ''))
    rule_map = {
        '__cc': re.compile(r'.*(\.cc|.c)'),
        '__cpp': re.compile(r'.*(\.cpp|.c\+\+)'),
    }
    for key, value in target.pop('rule_map', {}).items():
        rule_map[key] = config_ctx.format(value)


    keys = rule_map.keys()
    for key in keys:
        value = rule_map[key]
        if isinstance(value, (str, unicode, )) and not isinstance(value, RE_PATTERN_TYPE):
            rule_map[key] = re.compile(value)

    target_map = config_ctx['__target_map']
    deps, dep_flags, dep_ldflags = find_dependencies(config_ctx, ninja_path, dependencies)
    cflags += dep_flags
    cppflags += dep_flags
    ldflags += dep_ldflags

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
        paths = get_rel_glob_path(config_ctx, ninja_path, source)
        source_paths += paths
        build_rule = None
        for p in paths:
            object_path = calc_temp_path(config_ctx, p + '.o')
            object_paths.append(object_path)
            for rule, pattern in rule_map.items():
                if pattern.match(p):
                    build_rule = rule
                    break
            if build_rule is None:
                raise StandardError('Can not map rule for source: ' + p)
            flags = ''
            if build_rule == '__cc':
                flags = cflags
            if build_rule == '__cpp':
                flags = cppflags
            ninja_writer.build(
                object_path, build_rule,
                inputs=p,
                variables={
                    build_rule + '_flags': flags,
                },
            )
    inputs = list(object_paths)

    if type_name == 'executable':
        ldflags += ' -execute'
        output_path = calc_temp_path(config_ctx, os.path.join('bin', name))
        if OS == 'windows' and not output_path.endswith('.exe'):
            output_path += '.exe'
        ninja_writer.build(
            output_path, '__ld',
            inputs=inputs + deps,
            variables={
                '__ld_flags': ldflags,
            },
        )
        ninja_writer.build(
            name, 'phony',
            inputs=output_path
        )
    elif type_name == 'dynamic_library':
        ldflags += ' -dynamic'
        output_path = calc_temp_path(config_ctx, os.path.join('lib', name))
        if OS == 'windows':
            if not output_path.endswith('.dll'):
                output_path += '.dll'
        else:
            if not output_path.endswith('.so'):
                output_path += '.so'
        ninja_writer.build(
            output_path, '__ld',
            inputs=inputs + deps,
            variables={
                '__ld_flags': ldflags,
            },
        )
        ninja_writer.build(
            name, 'phony',
            inputs=output_path
        )
    elif type_name == 'static_library':
        ldflags += ' -s'
        ldflags += ' -static'
        output_path = calc_temp_path(config_ctx, os.path.join('lib', name))
        if not output_path.endswith('.a'):
            output_path += '.a'
        ninja_writer.build(
            output_path, '__ld',
            inputs=inputs + deps,
            variables={
                '__ld_flags': ldflags,
            },
        )
        ninja_writer.build(
            name, 'phony',
            inputs=output_path
        )
    else:
        raise StandardError('unknown target type: ' + type_name)

def write_ninja(config_ctx, ninja_path, ninja_writer):
    keys = config_ctx.keys()
    key_map_fn = {
        'build': write_build_ninja,
        'pool': write_pool_ninja,
        'rule': write_rule_ninja,
        'target': write_target_ninja,
    }
    keys_contains_name = ['pool', 'rule', 'target', ]
    plugins = config_ctx.get('plugin', [])
    for plugin in plugins:
        if not 'name' in plugin:
            raise StandardError('plugin require name field!')
        if not 'path' in plugin:
            raise StandardError('plugin require path field!')
        plugin_name = plugin['name']
        plugin_path = plugin['path']
        if plugin_path.endswith('.py'):
            raise StandardError('plugin path is not a python file!')
        plugin_path = get_rel_path(config_ctx, ninja_path, plugin_path)
        if plugin_path is None:
            raise StandardError('plugin path is not a exists!')
        register_library_plugin(plugin_name, plugin_path)

    for key in keys:
        value = config_ctx[key]
        if isinstance(value, (list, tuple, set, )):
            if key in keys_contains_name:
                data_map = {}
                for data in value:
                    if not 'name' in data:
                        raise StandardError(key + ' require name field!')
                    name = data['name']
                    if name in data_map:
                        raise StandardError(key + ' name conflit: ' + name)
                    data_map[name] = data
                config_ctx['__' + key + '_map'] = data_map
            if key in key_map_fn:
                for data in value:
                    key_map_fn[key](config_ctx, ninja_path, ninja_writer, data)
        if key == 'default' or key == 'include' or key == 'subninja':
            pass ## write at last
        else: # others is variable
            if key.startswith('__'):
                continue
            if not isinstance(value, (str, unicode, int, bool, float, )):
                continue
            ninja_writer.variable(key, value)

    if 'include' in config_ctx:
        key = 'include'
        value = config_ctx['include']
        if isinstance(value, (str, unicode, list, set, tuple, )):
            if isinstance(value, (str, unicode,)):
                write_include_ninja(config_ctx, ninja_path, ninja_writer, value)
        if isinstance(value, (list, set, tuple, )):
            for data in value:
                if isinstance(data, (str, unicode,)):
                    write_include_ninja(config_ctx, ninja_path, ninja_writer, data)

    if 'subninja' in config_ctx:
        key = 'subninja'
        value = config_ctx['subninja']
        if isinstance(value, (str, unicode, list, set, tuple, )):
            if isinstance(value, (str, unicode,)):
                write_subninja_ninja(config_ctx, ninja_path, ninja_writer, value)
        if isinstance(value, (list, set, tuple, )):
            for data in value:
                if isinstance(data, (str, unicode,)):
                    write_subninja_ninja(config_ctx, ninja_path, ninja_writer, data)
    
    if 'default' in config_ctx:
        key = 'default'
        value = config_ctx['default']
        if isinstance(value, list):
            items = []
            for item in value:
                if isinstance(item, (str, unicode,)):
                    items.append(item)
            ninja_writer.default(items)
        if isinstance(value, (str, unicode,)):
            ninja_writer.default([value, ])


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
    if not os.path.exists(ninja_path):
         generate_ninja(config_ctx, ninja_path)

def build_ninja(config_ctx, ninja_path):
    jobs = config_ctx.get('jobs', multiprocessing.cpu_count())
    child_ninja = subprocess.Popen(
        ['ninja' , '-f', ninja_path, '-j', str(jobs)]
    )
    sys.exit(child_ninja.wait())

def config_context(options):
    if '__change_dir' in options:
        os.chdir(options['__change_dir'])
    config_file = options.get('__config', os.path.join(os.path.curdir, 'build.toml'))
    if not os.path.isfile(config_file):
        raise IOError("config file not found: " + config_file)
    config = {}
    with open(config_file, 'r') as conf_file:
        config = toml.loads(conf_file.read())
    config_ctx = ContextDict(config)
    temp_path = config_ctx.pop('temp_path', None)
    if temp_path is not None:
        config_ctx.set('__temp_path', temp_path)
    config_ctx.update(options)
    return config_ctx

def generate(options, config_ctx=None):
    if config_ctx is None:
        config_ctx = config_context(options)
    temp_path = config_ctx.getOrDefault('__temp_path', os.path.join(os.path.curdir, 'build'))
    ensure_dir(temp_path)
    ninja_path = os.path.join(temp_path, 'build.ninja')
    is_force = config_ctx.getOrDefault('__force_generate', False)
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
    temp_path = config_ctx.getOrDefault('__temp_path', os.path.join(os.path.curdir, 'build'))
    os.remove(temp_path)


import plugins
for name, plugin in plugins.ALL_LIBRARY_PLUGINS.items():
    register_library_plugin(name, plugin)