#!/usr/bin/env python3
#
# Copyright 2014-2024 Justin Ottley
#
# Licensed under the terms set forth in the LICENSE.txt file
#

import os
import sys
import json
import shutil
import pprint
import argparse
import tempfile
import subprocess

if not os.listdir(os.getenv('RLP_FS_ROOT')):
    print('Error: Dir not available: {}'.format(os.getenv('RLP_FS_ROOT')))
    sys.exit(1)


scaffold_dir = os.path.dirname(os.path.dirname(__file__))
tmap_config_dir = os.path.join(scaffold_dir, 'lib', 'python3.11', 'site-packages', 'scaffold', 'ext', 'sclib', 'translation_config')
tmap_list = [
    os.path.join(tmap_config_dir, 'local'),
    os.path.join(tmap_config_dir, 'network'),
    os.path.join(tmap_config_dir, 'dev')
]

if not os.getenv('SC_TRANSLATION_MAP_PATH'):
    print('Setting SC_TRANSLATION_MAP_PATH')
    os.environ['SC_TRANSLATION_MAP_PATH'] = os.pathsep.join(tmap_list)
    print(tmap_list)

from rlp.core.net.websocket.standalone import StandaloneWsClient

from scaffold.ext import sset_release


def main():

    fs_root = os.getenv('RLP_FS_ROOT')
    if not fs_root:
        print('ERROR: RLP_FS_ROOT not set, aborting')
        sys.exit(sset_release.ERR_FS_NOT_AVAILABLE)
        return


    parser = argparse.ArgumentParser('')
    parser.add_argument(
        '--server',
        default=os.getenv('RLP_FS_REMOTE', 'wss://127.0.0.1:8003')
    )

    subparsers = parser.add_subparsers()

    p_info = subparsers.add_parser(
        'info',
        help='get info about a build'
    )

    p_info.add_argument('--project')

    p_info.add_argument('--build_version')

    p_info.set_defaults(func=sset_release.print_info)


    #
    # Software Set release
    #

    p_sset = subparsers.add_parser(
        'sset',
        help='release a software set'
    )

    p_sset.add_argument(
        '--project',
        required=True
    )

    p_sset.add_argument(
        '--config',
        dest='config_path',
        help='Full path to sc_config.json',
        required=True
    )

    p_sset.add_argument(
        '--sset',
        help='Software Set Name'
    )

    p_sset.add_argument(
        '--release_num',
        help='release_num, automatically determined if not specified',
        default=None
    )

    p_sset.set_defaults(func=sset_release.release_sset)


    #
    # build (description)
    #

    p_build = subparsers.add_parser(
        'build',
        help='release a build'
    )

    p_build.add_argument(
        '--site',
        default='rlp_test'
    )

    p_build.add_argument(
        '--project',
        help='project',
        required=True
    )


    p_build.add_argument(
        '--version',
        help='Build Version',
        required=True
    )

    p_build.add_argument(
        '--config',
        dest='config_path',
        help='full path to sc_config.json'
    )


    p_build.set_defaults(func=sset_release.release_build)


    #
    # Link a build software set to a release
    #

    p_link = subparsers.add_parser(
        'link',
        help='link a software set to a release'
    )

    p_link.add_argument(
        '--project'
    )

    p_link.add_argument(
        '--build_version'
    )

    p_link.add_argument(
        '--sset_version',
        default='0.0',
        help='Software Set Major Version'
    )

    p_link.add_argument(
        '--sset_project',
        default=None,
        help='Software Set Project if different from build project'
    )

    p_link.add_argument(
        '--release_num',
        help='Software Set Release Number'
    )

    p_link.add_argument(
        '--sset',
        help='Software Set Name'
    )

    p_link.set_defaults(func=sset_release.link_sset)

    #
    # Zip localization management
    #

    p_zip = subparsers.add_parser(
        'zip',
        help='create localization zips'
    )

    p_zip.add_argument(
        '--project'
    )

    p_zip.add_argument(
        '--config',
        dest='config_path'
    )

    p_zip.add_argument(
        '--sset'
    )

    p_zip.add_argument(
        '--release_num',
        default=None
    )

    p_zip.set_defaults(func=sset_release.zip_build)

    args = parser.parse_args()

    print('Attempting connection to: {}'.format(args.server))

    sset_release.edbc = StandaloneWsClient.init(args.server) # , encrypted=True)
    sset_release.edbc.connect()

    args.func(args)



if __name__ == '__main__':
    main()