#!/usr/bin/env python3
#
# Copyright 2014-2024 Justin Ottley
#
# Licensed under the terms set forth in the LICENSE.txt file
#

import os
import sys
import json
import argparse
import tempfile

import scaffold.variant


def _get_all_ssets(platform_target):

    sc_config_path = 'inst/{}/sc_config.json'.format(platform_target)
    sc_config = None
    if not os.path.isfile(sc_config_path):
        print('Error: Not found: {}, aborting'.format(sc_config_path))
        sys.exit(1)


    with open(sc_config_path) as wfh:
        print('Reading {}'.format(sc_config_path))
        sc_config = json.load(wfh)
    
    sset_list = []
    for sset_name, sset_config in sc_config.items():
        if sset_config.get('sftset_type') == 'int':
            sset_list.append(sset_name)

    return sset_list


def run_build(target_list, args):

    platform_target = scaffold.variant.get_variant('platform_target')
    ninja_out = 'include build/gen/{}/rules.ninja\n\n'.format(platform_target)
    for target_entry in target_list:
        ninja_out += 'include build/gen/{}/build_{}.ninja\n'.format(
            platform_target, target_entry)


    print(ninja_out)

    temp_fd, temp_filename = tempfile.mkstemp(prefix='scninja_build_', suffix='.ninja')
    os.close(temp_fd)
    with open(temp_filename, 'w') as wfh:
        wfh.write(ninja_out)
    
    cmd = 'ninja'
    if args.verbose:
        cmd += ' -v'

    if args.dry_run:
        cmd += ' -n'

    cmd = '{} -f {}'.format(cmd, temp_filename)
    print(cmd)
    os.system(cmd)
    # os.remove(temp_filename)


def main():

    parser = argparse.ArgumentParser('')
    parser.add_argument('-t', '--targets', default=None)
    parser.add_argument('-v', '--verbose', action='store_true', default=False)
    parser.add_argument('-n', '--dry-run', action='store_true', default=False, dest='dry_run')
    parser.add_argument('--platform_target', default=None)

    args = parser.parse_args()

    platform_target = args.platform_target
    if not platform_target:
        platform_target = scaffold.variant.get_variant('opsys')

    scaffold.variant.register_variant('platform_target', platform_target)

    target_list = []
    if args.targets:
        target_list = args.targets.split(',')
        target_list = [t.strip() for t in target_list]

    else:
        target_list = _get_all_ssets(platform_target)


    run_build(target_list, args)


if __name__ == '__main__':
    main()