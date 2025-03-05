#
# Copyright 2014-2024 Justin Ottley
#
# Licensed under the terms set forth in the LICENSE.txt file
#

import os
import sys
import platform

import scaffold.variant

from . import shared_library

def configure_env(benv):
    shared_library.configure_env(benv)

    if 'wasm' not in scaffold.variant.get_variant('platform_target'):
        benv.shlib_inst_dir = os.path.join(
            benv.inst_top_dir, benv.sset_name, benv.py_reldir
        )

        benv.env['SHLIBPREFIX'] = ''


def configure_builders(benv):
    shared_library.configure_builders(benv)

    # we need this so that all dependent libs end up linked in
    if os.name == 'posix' and platform.system() != 'Darwin':
        benv.env['CC_EXTRA_FLAGS'] += '-Wl,--no-as-needed'
