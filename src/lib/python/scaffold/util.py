#
# Copyright 2014-2024 Justin Ottley
#
# Licensed under the terms set forth in the LICENSE.txt file
#

import os
import shutil
import logging
import tempfile
import importlib
import importlib.util

import subprocess

LOG = logging.getLogger(__name__)

def import_module(module_ns):
    
    top_module = __import__(module_ns)
    
    for entry in module_ns.split('.')[1:]:
        top_module = getattr(top_module, entry)
        
    return top_module


def import_object(object_ns):
    
    object_ns_parts = object_ns.split('.')
    object_module = '.'.join(object_ns_parts[:-1])
    object_module = import_module(object_module)
    
    importlib.reload(object_module)
    
    return getattr(object_module, object_ns_parts[-1])


def load_module_without_import(module_ns, module_path):

    module_spec = importlib.util.spec_from_file_location(module_ns, module_path)
    module_obj = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module_obj)

    return module_obj


def deep_merge(new_dict, result_dict, list_method='replace'):
    '''
    perform a "deep" merge of two nested dictionaries. Currently this is
    intentionally restricted to dicts, hence the use of isinstance().
    '''
    
    for key in new_dict:
        if key in result_dict:
            
            if isinstance(new_dict[key], dict) and \
            isinstance(result_dict[key], dict):
                
                # recurse
                deep_merge(new_dict[key], result_dict[key])
                
                
            elif isinstance(result_dict[key], dict) and not \
            isinstance(new_dict[key], dict):
                
                raise Exception('cannot merge, incompatible types - {k}'.format(
                    k=key))
                
                
            elif isinstance(new_dict[key], list) and \
            isinstance(result_dict[key], list) and \
            list_method == 'add':
                
                # don't recurse into lists for now, just combine
                
                for entry in new_dict[key]:
                    if entry not in result_dict[key]:
                        
                        LOG.debug('adding list item {item}'.format(
                            item=entry))
                            
                        result_dict[key].append(entry)
                        
            else:
                result_dict[key] = new_dict[key]
                
        else:
            
            # add the new value to the result
            result_dict[key] = new_dict[key]



def do_subst(src_path, dest_path, src_map_list):

    dest_prefix, dest_ext = os.path.splitext(dest_path)
    temp_fd, temp_filename = tempfile.mkstemp(suffix=dest_ext)

    with open(src_path) as sfh:
        for line in sfh.readlines():
            new_line = line
            for src_string, dest_string in src_map_list:
                new_line = new_line.replace(src_string, dest_string)
            os.write(temp_fd, bytes(new_line, 'utf8'))

    LOG.debug('{} -> {} -> {}'.format(src_path, temp_filename, dest_path))
    shutil.copy(temp_filename, dest_path)


def copy_file(src, dest, recursive=False, noop=False):

    cmd = 'cp'
    if recursive:
        cmd += ' -R'

    if os.name == 'nt':
        cmd = 'copy'
        if recursive:
            cmd = 'xcopy /E /Y /I'

    cmd = '{} "{}" "{}"'.format(cmd, src, dest)
    LOG.info(cmd)

    if not noop:
        result = subprocess.run(cmd, shell=True)
        return result.returncode


def get_inst_dir():

    currdir = os.path.dirname(__file__)
    for _ in range(4):
        currdir = os.path.dirname(currdir)
    
    return currdir