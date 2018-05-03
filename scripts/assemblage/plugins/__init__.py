#!/usr/bin/env python2
# -*- coding: UTF-8 -*-





__all__ = [
    'ALL_LIBRARY_PLUGINS',
]

from lib_pkg_config import find as lib_pkg_config
from lib_fltk_config import find as lib_fltk_config
from lib_llvm_config import find as lib_llvm_config
from lib_odbc_config import find as lib_odbc_config
from lib_wx_config import find as lib_wx_config

ALL_LIBRARY_PLUGINS = {
    'pkg-config': lib_pkg_config,
    'fltk-config': lib_fltk_config,
    'llvm-config': lib_llvm_config,
    'odbc_config': lib_odbc_config,
    'wx-config': lib_wx_config,
}

