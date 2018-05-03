#!/usr/bin/env python2
# -*- coding: UTF-8 -*-


import os
import tempfile

from __init__ import detect_c_magic_flags
from __init__ import detect_cpp_magic_flags
from __init__ import detect_as_c_magic_flags
from __init__ import detect_as_cpp_magic_flags
from __init__ import detect_obj_magic_flags
from __init__ import detect_ld_magic_flags
from ContextDict import ContextDict




def test(cc_path, cpp_path):
    temp_path = tempfile.gettempdir()
    config_ctx = ContextDict({
        '__temp_path': temp_path
    })
    ninja_path = os.path.join(temp_path, 'build.ninja')

    print '========== detect_c_magic_flags =========='
    ret = detect_c_magic_flags(config_ctx, ninja_path, cc_path)
    print ret, '\n'
    assert len(ret) > 0

    print '========== detect_cpp_magic_flags =========='
    ret = detect_cpp_magic_flags(config_ctx, ninja_path, cpp_path)
    print ret, '\n'
    assert len(ret) > 0

    print '========== detect_as_c_magic_flags =========='
    ret = detect_as_c_magic_flags(config_ctx, ninja_path, cc_path)
    print ret, '\n'
    assert len(ret) > 0

    print '========== detect_as_cpp_magic_flags =========='
    ret = detect_as_cpp_magic_flags(config_ctx, ninja_path, cpp_path)
    print ret, '\n'
    assert len(ret) > 0

    print '========== detect_obj_magic_flags =========='
    ret = detect_obj_magic_flags(config_ctx, ninja_path, cc_path)
    print ret, '\n'
    assert len(ret) > 0

    print '========== detect_ld_magic_flags =========='
    ret = detect_ld_magic_flags(config_ctx, ninja_path, cc_path)
    print ret, '\n'
    assert len(ret) > 0

    print config_ctx
    



def main():
    # print '==========================================='
    # print '================== clang =================='
    # print '==========================================='
    # test(
    #     '/usr/bin/cc',
    #     '/usr/bin/c++'
    # )
    # print ''
    # print ''

    print '==========================================='
    print '================== clang =================='
    print '==========================================='
    test(
        '/Users/tajoy-macbookpro/gcc/usr/local/bin/gcc',
        '/Users/tajoy-macbookpro/gcc/usr/local/bin/g++'
    )

if __name__ == '__main__':
    main()