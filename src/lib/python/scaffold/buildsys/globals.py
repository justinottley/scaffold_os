#
# Copyright 2014-2024 Justin Ottley
#
# Licensed under the terms set forth in the LICENSE.txt file
#

import os
import platform
from .. import variant as scaffoldvariant


# commandline args
args = {}

platform_str = scaffoldvariant.get_platform()
senv_config = {}

build_time = None


# TODO FIXME HACK
_RULES_DONE = False

def _init_senv_config():

    global senv_config

    rlp_root = '/home/justinottley/dev/revlens_root'
    if os.name == 'nt':
        rlp_root = r'C:\Users\justi\dev\revlens_root'
    if platform.system() == 'Darwin':
        rlp_root = '/Users/justinottley/dev/revlens_root'
        
    if scaffoldvariant.get_variant('arch') == 'aarch64': # termux
        rlp_root = '{}/dev/revlens_root'.format(os.getenv('HOME'))

    tb_version = '22_09'
    thirdbase_root = os.path.join(rlp_root, 'thirdbase', tb_version)
    thirdbase_dir = os.path.join(thirdbase_root, platform_str)

    qt_version = '6.8.2'

    senv_config.update({
        'site_name': 'rlp',
        'dir.rlp_root': rlp_root,
        'dir.thirdbase_root': thirdbase_root,
        'dir.thirdbase': thirdbase_dir,
        'qt_version': qt_version
    })


_init_senv_config()
del _init_senv_config
