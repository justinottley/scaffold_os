#
# Copyright 2014-2024 Justin Ottley
#
# Licensed under the terms set forth in the LICENSE.txt file
#

import os
import pprint
import logging

LOG = logging.getLogger(__name__)


def which(exec_name, env=None):
    '''
    An in-process implementation of the shell command "which", to locate
    an executable along a search path (typically the $PATH env. variable)
    '''


    # leveraging python scope leaking..
    if env:
        path_list = env['PATH']

    else:
        path_list = os.environ['PATH'].split(os.pathsep)

    for path_entry in path_list:
        exec_fullpath = os.path.join(path_entry, exec_name)
        if os.path.isfile(exec_fullpath):
            return exec_fullpath


def get_exec_path(exec_dir, exec_name):
    '''
    A helper routine to help produce the correct executable extension
    for an executable application (especially on windows)
    '''

    exec_path = os.path.join(exec_dir, exec_name)

    if os.name == 'nt':
        win_suffixes = ['.exe', '.bat']
        for suffix_entry in win_suffixes:
            exec_path += suffix_entry
            if os.path.exists(exec_path):
                return exec_path

    else:
        return exec_path


def split_path(path_in):

    # remove aany leading slashes
    start_idx = 0
    for char in path_in:
        if char not in ['/', '\\']:
            break
        
        start_idx += 1
    
    result = []

    for entry in path_in[start_idx:].split('/'):
        for sub_entry in entry.split('\\'):
            result.append(sub_entry)

    return result


def validate_path_exists(formatted_path, path_info, style_handler, translation_map):
    '''
    A path validator that returns True if the path exists on the filesystem
    Used in translation map system.

    NOTE: function signature is complete as an example for hte translation map API,
    only 1st arg (formatted_path) used here
    '''

    if formatted_path:
        
        # NOTE: hmm. the path coming in might be a URI. What should be done in this case?
        #
        if style_handler.name == 'URI':
            formatted_path = '{}{}{}'.format(
                os.path.sep.join(path_info.anchor_list),
                os.path.sep,
                os.path.sep.join(path_info.path_list)
            )
            
            # print(forged_path)

        formatted_path_exists = os.path.exists(formatted_path)

        LOG.log(9, 'Check if exists on disk: {} - {} - OSName: {}'.format(
            formatted_path, formatted_path_exists, os.name))

        return formatted_path_exists

    return False


def to_bool(value_in):

    type_val_in = type(value_in)
    result = False

    if type_val_in == bool:
        result = value_in

    elif type_val_in == int:
        result = (value_in > 0)

    elif issubclass(value_in.__class__, str):
        result = any([
            value_in == 'true',
            value_in == 'True',
            value_in == '1',
            value_in == 'on',
            value_in == 'yes'
        ])

    return result

