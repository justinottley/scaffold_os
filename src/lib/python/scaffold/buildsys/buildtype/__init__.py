#
# Copyright 2014-2024 Justin Ottley
#
# Licensed under the terms set forth in the LICENSE.txt file
#

from .. import util as buildsys_util

import scaffold.buildsys.globals as buildsys_globals

def get_buildtype_lib(lib_name):

    if lib_name == 'python_shlib_extension_module':
        if buildsys_globals.args.get('pybind_mode') == 'static':
            lib_name = 'shared_library'

        else:
            lib_name = 'python_extension_module'


    mod_ns = '{}.{}'.format(__name__, lib_name)
    mod = buildsys_util.import_module(mod_ns)
    return mod