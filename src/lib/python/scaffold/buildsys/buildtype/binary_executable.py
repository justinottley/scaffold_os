#
# Copyright 2014-2024 Justin Ottley
#
# Licensed under the terms set forth in the LICENSE.txt file
#

import os

from . import shared_library
from scaffold.buildsys import buildlib

def configure_env(benv):
    benv.lib_name = '' # flag to skip shared library builders like copy headers, etc

    shared_library.configure_env(benv)

    benv.sset_gen_lib_dir = os.path.join(benv.sset_gen_dir, 'lib', benv.executable_name)
    benv.bin_inst_dir = os.path.join(benv.sset_inst_dir, 'bin')


def configure_builders(benv):
    b_o = shared_library._configure_builders(benv)

    bl_opsys = buildlib.get_lib('OpSys')
    b_exe = benv.register_builder(bl_opsys.builder('CompiledExecutable'), b_o)

    return b_exe
