#!/usr/bin/env python3
#
# Copyright 2014-2024 Justin Ottley
#
# Licensed under the terms set forth in the LICENSE.txt file
#

import os
import sys
import logging
import tempfile
import platform
import argparse

py_version = '.'.join(platform.python_version_tuple()[0:2])
lib_dir = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    'lib',
    'python{}'.format(py_version),
    'site-packages'
)

sys.path.insert(0, lib_dir)

LOG_FORMATTER = logging.Formatter(
        '%(name)-10s [ %(levelname)s ] : %(message)s')

def _init_logging():

    rl = logging.getLogger('')
    rl.setLevel(1)

    logfilename = 'scaffold.log'
    if os.name == 'nt':
        logfilename = 'scaffold.log.{}'.format(os.getpid())

    fh = logging.FileHandler(os.path.join(tempfile.gettempdir(), logfilename))
    fh.setFormatter(LOG_FORMATTER)

    rl.addHandler(fh)
    # sh = logging.StreamHandler()
    # sh.setLevel(1)

    # rl.addHandler(sh)



def clone_superproject(args):

    rl = logging.getLogger('')
    
    sh = logging.StreamHandler()
    sh.setFormatter(LOG_FORMATTER)

    rl.addHandler(sh)

    from scaffold.builder import Builder

    b = Builder(args.git_url, base_dir=args.dest)
    b.clone_superproject()

    # b.build_superproject()


def init_env(args):
    from scaffold.env.cntrl import EnvController

    cntrl = EnvController(args.config_path, args.config_loader)

    commands = ''

    if os.name == 'nt':
        commands = 'cmd'

    env_file = cntrl.generate_env_file(
        messages=[],
        extra_commands=commands)

    print(str(env_file))




def main():

    _init_logging()

    parser = argparse.ArgumentParser('Scaffold')

    subparsers = parser.add_subparsers(help='sub-command help')

    #
    # Clone
    #

    p_clone = subparsers.add_parser(
        'clone',
        help='Clone a superproject'
    )

    p_clone.add_argument(
        '--dest',
        help='destination to clone to, default current directory',
        default=os.getcwd()
    )

    p_clone.add_argument(
        '--build_flavour',
        default='master',
        help='build flavour'
    )

    p_clone.add_argument(
        '--branch',
        default='master',
        help='git branchh to checkout'
    )

    p_clone.add_argument(
        'git_url',
        help='Git URL to clone',
        default='git@bitbucket.org:justinottley/sp_revsix.git'
    )

    p_clone.set_defaults(func=clone_superproject)


    #
    # Init
    #

    p_init = subparsers.add_parser(
        'init',
        help='Initialize an environment'
    )

    p_init.add_argument(
        '--loader',
        dest='config_loader',
        help='Loader to use for config loading (Build, Single)'
    )

    p_init.add_argument(
        'config_path',
        help='path to sc_config.json',
        default=None,
        nargs='?'
    )

    p_init.set_defaults(func=init_env)

    args = parser.parse_args()

    args.func(args)


if __name__ == '__main__':
    main()