#
# Copyright 2014-2024 Justin Ottley
#
# Licensed under the terms set forth in the LICENSE.txt file
#

from scaffold.buildsys import buildlib

def configure_env(benv):
    pass


def configure_builders(benv):
    bl_opsys = buildlib.get_lib('OpSys')
    b_sfiles = benv.register_builder(bl_opsys.builder('CopyStaticFiles'))

    return b_sfiles