#!/usr/bin/env python2
# -*- coding: UTF-8 -*-


import os
import sys
import re
import subprocess
import multiprocessing
import platform
import glob

import preconditions
import toml
import ninja

from ContextDict import ContextDict

RE_PATTERN_TYPE = None
if hasattr(re, '_pattern_type'):
    RE_PATTERN_TYPE = re._pattern_type
else:
    RE_PATTERN_TYPE = type(re.compile(''))


__all__ = [
    'build',
    'generate',
    'clean',
]

def calc_temp_path(config_ctx, path):
    temp_path = config_ctx.getOrDefault('__temp_path', os.path.join(os.path.curdir, 'build'))
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


def glob_in_path(curdir, glob_path):
    before_dir = os.curdir
    os.chdir(curdir)
    ret = glob.glob(glob_path)
    os.chdir(before_dir)
    return ret

def full_real_path(curdir, rel_path):
    before_dir = os.curdir
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

def embed_ninja(config_ctx, ninja_path, ninja_writer):
    cc_exec = config_ctx.get('__cc_exec', 'cc')
    cpp_exec = config_ctx.get('__cpp_exec', 'cpp')
    ld_exec = config_ctx.get('__ld_exec', 'ld')
    cc_path = config_ctx.get('__cc_path', None)
    cpp_path = config_ctx.get('__cpp_path', None)
    ld_path = config_ctx.get('__ld_path', None)
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

    if not exists_executable(cc_path):
        raise IOError('executable file not exists or can not execute:' + cc_exec)
    if not exists_executable(cpp_path):
        raise IOError('executable file not exists or can not execute:' + cpp_exec)
    if not exists_executable(ld_path):
        raise IOError('executable file not exists or can not execute:' + ld_exec)

    cc_flags = config_ctx.get('__cc_flags', '')
    cpp_flags = config_ctx.get('__cpp_flags', '')
    ld_flags = config_ctx.get('__ld_flags', '')

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
        new_ctx = config_ctx.clone().merge({
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

def write_target_ninja(config_ctx, ninja_path, ninja_writer, data):
    target = dict(data)
    conditions = config_ctx.format(target.pop('conditions', []))

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
    sources = config_ctx.format(target.pop('sources', []))
    dependencies = config_ctx.format(target.pop('dependencies', []))
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
    inputs = list(object_paths)

    target_map = config_ctx['__target_map']
    dependency_target = None
    for dependency in dependencies:
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
        if dependency_target is not None:
            type_name = dependency_target['type']
            if type_name == 'executable':
                raise StandardError('can not dependency on a executable: ' + dependency)
            elif type_name == 'dynamic_library':
                dependency_path = calc_temp_path(config_ctx, os.path.join('lib', name))
                if OS == 'windows':
                    if not dependency_path.endswith('.dll'):
                        dependency_path += '.dll'
                else:
                    if not dependency_path.endswith('.so'):
                        dependency_path += '.so'
                ldflags += ' -L"%s"' % (os.path.dirname(dependency_path))
                dependency_name = os.path.basename(dependency_path)
                if dependency_name.startswith('lib'):
                    dependency_name = dependency_name[3:]
                if dependency_name.endswith('.so'):
                    dependency_name = dependency_name[:-3]
                if dependency_name.endswith('.dll'):
                    dependency_name = dependency_name[:-4]
                ldflags += ' -l"%s"' % (os.path.basename(dependency_name))
                ldflags += ' -rpath"%s"' % (os.path.dirname(dependency_path))
            elif type_name == 'static_library':
                dependency_path = calc_temp_path(config_ctx, os.path.join('lib', name))
                if OS == 'windows':
                    if not dependency_path.endswith('.dll'):
                        dependency_path += '.dll'
                else:
                    if not dependency_path.endswith('.so'):
                        dependency_path += '.so'
                ldflags += ' -L"%s"' % (os.path.dirname(dependency_path))
                dependency_name = os.path.basename(dependency_path)
                if dependency_name.startswith('lib'):
                    dependency_name = dependency_name[3:]
                if dependency_name.endswith('.so'):
                    dependency_name = dependency_name[:-3]
                if dependency_name.endswith('.dll'):
                    dependency_name = dependency_name[:-4]
                ldflags += ' -l"%s"' % (os.path.basename(dependency_name))
            else:
                raise StandardError('unknown target type: ' + type_name)

    if type_name == 'executable':
        ldflags += ' -execute'
        output_path = calc_temp_path(config_ctx, os.path.join('bin', name))
        if OS == 'windows' and not output_path.endswith('.exe'):
            output_path += '.exe'
        ninja_writer.build(
            output_path, '__ld',
            inputs=' '.join(inputs),
            variables={
                '__ld_flags': ldflags,
            },
        )
    elif type_name == 'dynamic_library':
        ldflags += ' -dynamic'
        output_path = calc_temp_path(config_ctx, os.path.join('lib', name))
        if OS == 'windows':
            if output_path.endswith('.dll'):
                output_path += '.dll'
        else:
            if not output_path.endswith('.so'):
                output_path += '.so'
        ninja_writer.build(
            output_path, '__ld',
            inputs=' '.join(inputs),
            variables={
                '__ld_flags': ldflags,
            },
        )
    elif type_name == 'static_library':
        ldflags += ' -static'
        output_path = calc_temp_path(config_ctx, os.path.join('lib', name))
        if output_path.endswith('.a'):
            output_path += '.a'
        ninja_writer.build(
            output_path, '__ld',
            inputs=' '.join(inputs),
            variables={
                '__ld_flags': ldflags,
            },
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

        if key == 'default':
            if isinstance(value, list):
                items = []
                for item in value:
                    if isinstance(item, (str, unicode,)):
                        items.append(item)
                ninja_writer.default(items)
            if isinstance(value, (str, unicode,)):
                ninja_writer.default([value, ])
        elif key == 'include' or key == 'subninja':
            if not isinstance(value, (str, unicode, list, set, tuple, )):
                continue
            if isinstance(value, (str, unicode,)):
                if key == 'include':
                    write_include_ninja(config_ctx, ninja_path, ninja_writer, value)
                if key == 'subninja':
                    write_subninja_ninja(config_ctx, ninja_path, ninja_writer, value)
        else: # others is variable
            if key.startswith('__'):
                continue
            if not isinstance(value, (str, unicode, int, bool, float, )):
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
