#
# Copyright 2014-2024 Justin Ottley
#
# Licensed under the terms set forth in the LICENSE.txt file
#

import os
import subprocess


def _run_cmd(cmd_list, path=None):

    cwd = os.getcwd()
    if path:
        os.chdir(path)

    r = subprocess.run(cmd_list, capture_output=True)
    result = r.stdout.decode('utf-8').strip()

    os.chdir(cwd)

    return result


def get_url(path=None):
    return _run_cmd(['git', 'remote', 'get-url', '--all', 'origin'], path=path)


def get_branch(path=None):
    return _run_cmd(['git', 'branch', '--show-current'], path=path)


def get_repo_dirname(repo_url):
    return os.path.splitext(os.path.basename(repo_url.split(':')[1]))[0]
