#!/usr/bin/env python3
#
# Copyright 2014-2024 Justin Ottley
#
# Licensed under the terms set forth in the LICENSE.txt file
#

import os
import sys
import argparse

import scaffold.variant
from scaffold.buildsys.runtime import ScNinjaRuntime
import scaffold.buildsys.globals as sc_globals


def main():

    parser = argparse.ArgumentParser('')
    # parser.add_argument('--config', default=True, action='store_true')
    parser.add_argument('--platform_target', default=None)
    parser.add_argument('--pybind_mode', default='static')

    args = parser.parse_args()

    platform_target = args.platform_target
    if not platform_target:
        platform_target = scaffold.variant.get_variant('opsys')

    scaffold.variant.register_variant('platform_target', platform_target)

    platform_target_gen_dir = 'build/gen/{}'.format(platform_target)
    if not os.path.isdir(platform_target_gen_dir):
        print('Creating {}'.format(platform_target_gen_dir))
        os.makedirs(platform_target_gen_dir)

    platform_target_inst_dir = 'inst/{}'.format(platform_target)
    if not os.path.isdir(platform_target_inst_dir):
        print('Creating {}'.format(platform_target_inst_dir))
        os.makedirs(platform_target_inst_dir)


    sc_globals.args['pybind_mode'] = args.pybind_mode


    scr = ScNinjaRuntime(True) # gen_config=args.config)
    scr.run('ScaffoldScript')


if __name__ == '__main__':
    main()