#
# Copyright 2014-2024 Justin Ottley
#
# Licensed under the terms set forth in the LICENSE.txt file
#

import os
import sys
import json
import pprint
import logging
import traceback

import importlib

from .. import util as scaffold_util


from .sset import (
    SoftwareSet,
    SclibSoftwareSet,
    BuildRelpathSoftwareSet,
    ExternalSoftwareSet,
    ThirdbaseSoftwareSet,
    AppSoftwareSet
)

class SoftwareSetManager(object):

    def __init__(self, build_config, config_path=None):

        self.LOG = logging.getLogger('{}.{}'.format(self.__class__.__module__, self.__class__.__name__))

        self.config = build_config
        self.config_path = config_path

        self._software_sets = {}
        self._module_cache = {}

        try:
            self._init()
            pass
        except:
            print(traceback.format_exc())


    @classmethod
    def init(cls, config_path=None):

        if config_path is None:
            config_path = os.getenv('SC_CONFIG_INIT_IN')


        build_config = None
        with open(config_path) as fh:
            build_config = json.load(fh)

        if build_config:
            return cls(build_config, config_path)

    @property
    def sclib_module(self):
        # import sclib
        # print('sclib module: {}'.format(sclib))

        # return sclib
        return self._module_cache.get('sclib')

    
    @property
    def config_bootstrap(self):
        return self.config['__bootstrap__']


    @property
    def project_name(self):
        return self.config_bootstrap['project']


    def _init_sset_obj(self, sset_name, sset_config):

        self.LOG.debug('_init_sset_obj() {}'.format(sset_name))


        if 'sftset_type' not in sset_config:
            raise Exception('{} - no sftset_type'.format(sset_name))

        sftset_type = sset_config['sftset_type']
        sftset_cls = SoftwareSet
        if 'sclib.cls' in sset_config:
            cls_ns = sset_config['sclib.cls']

            if cls_ns.startswith('scaffold'):
                sftset_cls = scaffold_util.import_object(cls_ns)

            else:
                parent_ns, _, cls_name = cls_ns.rpartition('.')

                self.LOG.debug('Checking module cache for module "{}"'.format(parent_ns))
                if parent_ns not in self._module_cache:
                    
                    # NOTE: must be under sclib namespace
                    #
                    parent_module = scaffold_util.load_module_without_import(parent_ns, self._sclib_module_path)
                    self._module_cache[parent_ns] = parent_module

                parent_module = self._module_cache[parent_ns]
                sftset_cls = getattr(parent_module, cls_name)


            self.LOG.debug('Loaded: {}'.format(sftset_cls))


        elif sftset_type == 'ext':
            sftset_cls = ExternalSoftwareSet

        elif sftset_type == 'tb':
            sftset_cls = ThirdbaseSoftwareSet

        elif sftset_type == 'app':
            sftset_cls = AppSoftwareSet

        elif sftset_type == 'int':
            sftset_cls = BuildRelpathSoftwareSet


        # instantiate
        sset_obj = sftset_cls(self, sset_name, sset_config)
        return sset_obj


    def _init(self):
        
        if 'sclib' in self.config:
            sclib_sset = SclibSoftwareSet(self, 'sclib', self.config['sclib'])
            self._sclib_module_path = os.path.join(sclib_sset.python_lib_dir, 'sclib', '__init__.py')

            self.LOG.debug(self._sclib_module_path)

            # sys.path.insert(0, sclib_sset.python_lib_dir)
            # import sclib
            # importlib.reload(sclib)

            sclib_module = scaffold_util.load_module_without_import('sclib', self._sclib_module_path)
            self._module_cache['sclib'] = sclib_module

            self.LOG.info('cached sclib module from {}'.format(self._sclib_module_path))

            sclib_sset._init_translation_map()

        for sset_name in self.config.keys():

            if sset_name in ['__bootstrap__']:
                continue

            self.LOG.info('Loading Software Set: {}'.format(sset_name))
            self.LOG.debug(pprint.pformat(self.config[sset_name]))
            self.LOG.debug('')

            sset_config = self.config[sset_name]
            sset_obj = self._init_sset_obj(sset_name, sset_config)
            self.LOG.debug('!!!!!!!!!!')
            self.LOG.debug(sset_obj)
            self._software_sets[sset_name] = sset_obj


    def get_software_set(self, sset_name):
        return self._software_sets[sset_name]

    def get_install_required(self, include_types=None, exclude_types=None, callback=None):

        localize_list = []
        for sset in self._software_sets.values():
            
            if exclude_types and sset.sset_type in exclude_types:
                print('SKIPPING {}'.format(sset.sftset_name))
                continue
            
            if include_types is None:

                print('CHECKING {}'.format(sset))
                localize_list.extend(sset.get_install_required(exclude_types=exclude_types))

            elif sset.sftset_type in include_types:
                localize_list.extend(sset.get_install_required(
                    include_types=include_types, exclude_types=exclude_types))

        return localize_list