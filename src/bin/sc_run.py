#!/usr/bin/env python3
#
# Copyright 2014-2024 Justin Ottley
#
# Licensed under the terms set forth in the LICENSE.txt file
#

import os
import sys
import argparse
import platform


py_version = '.'.join(platform.python_version_tuple()[0:2])
lib_dir = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    'lib',
    'python{}'.format(py_version),
    'site-packages'
)

sys.path.insert(0, lib_dir)

from scaffold.env.cntrl import EnvController


def run(args):


    cntrl = EnvController(args.config_path, args.config_loader)

    commands = args.command

    env_file = cntrl.generate_env_file(
        messages=[],
        extra_commands=commands)

    print(str(env_file))

    os.chmod(env_file, 0o0777)
    os.system(env_file)


def main():

    parser = argparse.ArgumentParser('sc command runner')

    parser.add_argument(
        '--config_path',
        required=True
    )

    parser.add_argument(
        '--config_loader',
        default=None
    )

    parser.add_argument('command')

    args = parser.parse_args()

    run(args)

if __name__ == '__main__':
    main()