#
# Copyright 2014-2024 Justin Ottley
#
# Licensed under the terms set forth in the LICENSE.txt file
#

import os
import json
import copy
import shutil
import logging
import tempfile

from collections import OrderedDict

import scaffold.util
import scaffold.variant

class ConfigLoaderError(Exception): pass

class ConfigLoader:

    SC_CONFIG_FILENAME = 'sc_config.json'
    SC_CONFIG_INIT_DIR = None

    TEMP_DIR = os.path.join(
        tempfile.gettempdir(),
        os.getenv('USER', os.getenv('USERNAME')),
        'vc',
        'env')
    
    def __init__(self, config=None, reset=False):
        self.LOG = logging.getLogger('{}.{}'.format(self.__class__.__module__, self.__class__.__name__))

        if not self.name:
            raise ConfigLoaderError('Base class use not allowed')

        self.config = config or {'export_env': {}}
        if reset:
            self.LOG.debug('Resetting class attribute ConfigLoader.SC_CONFIG_INIT_DIR')
            ConfigLoader.SC_CONFIG_INIT_DIR = None


    @property
    def name(self):
        return self.__class__.__name__.replace('ConfigLoader', '')


    def _get_platform_dir(self, parent_dir):

        if not os.path.isdir(parent_dir):
            self.LOG.debug('_get_platform_dir(): creating {d}'.format(d=parent_dir))
            os.makedirs(parent_dir)

        platform_dir = None
        platform_list = scaffold.variant.get_platform_list()

        for platform_entry in platform_list:
            _platform_dir = os.path.join(parent_dir, platform_entry)

            # self.LOG.debug('_get_platform_dir(): trying {d}'.format(d=_platform_dir))
            if os.path.isdir(_platform_dir):

                self.LOG.debug('_get_platform_dir(): FOUND {d}'.format(d=_platform_dir))
                platform_dir = _platform_dir
                break


        if not platform_dir:
            _default_platform_dir = os.path.join(parent_dir, platform_list[-1])
            self.LOG.debug('_get_platform_dir(): no existing platform dir found, creating default at {d}'.format(
                d=_default_platform_dir
            ))
            os.makedirs(_default_platform_dir)
            platform_dir = _default_platform_dir


        return platform_dir


    def _get_existing_init_dir(self):

        # try environment first, then try our own loaded value
        #
        existing_init_dir = os.getenv('SC_CONFIG_INIT_DIR')

        if existing_init_dir:

            if os.path.isdir(existing_init_dir):
                self.LOG.debug('init working config dir from environment')

            else:
                self.LOG.debug('got config dir from environment, but config dir does not exist: {c} - resetting'.format(
                    c=existing_init_dir))

                existing_init_dir = None
                del os.environ['SC_CONFIG_INIT_DIR']

        elif not existing_init_dir and \
        'export_env' in self.config and \
        'SC_CONFIG_INIT_DIR' in self.config['export_env'] and \
        os.path.isdir(self.config['export_env']['SC_CONFIG_INIT_DIR']):

            self.LOG.debug('init working config dir from current process object instance')
            existing_init_dir = self.config['export_env']['SC_CONFIG_INIT_DIR']


        elif ConfigLoader.SC_CONFIG_INIT_DIR is not None and \
        os.path.isdir(ConfigLoader.SC_CONFIG_INIT_DIR):

            self.LOG.debug('init working config dir from current process class attrib')
            existing_init_dir = ConfigLoader.SC_CONFIG_INIT_DIR

        return existing_init_dir


    def _init_default_config_dirs(self):

        self.LOG.debug('init user config dir')

        parent_config_dir = str(os.path.join(os.path.expanduser('~'), '.config', 'rlp', 'sc'))

        self.config['config_dir.user'] = self._get_platform_dir(parent_config_dir)

        self.LOG.debug('init working config dir')
        existing_init_dir = self._get_existing_init_dir()

        # create tmp config dir if not present
        #
        if existing_init_dir:

            self.LOG.debug('using existing working config dir: {d}'.format(d=existing_init_dir))

            tmp_config_dir = existing_init_dir
            
        else:

            if not os.path.isdir(self.TEMP_DIR):
                os.makedirs(self.TEMP_DIR)

            tmp_config_dir = tempfile.mkdtemp(prefix='vc_config_', dir=self.TEMP_DIR)

            self.LOG.debug('init new working config dir: {td}'.format(
                td=tmp_config_dir))



        # set vc_config_path to include the temp config dir
        #
        #
        # The export_env entry is what is written to the environment
        # so that subsequent processes (after this one exits) get the
        # temp dir.
        #
        self.config['export_env']['SC_CONFIG_INIT_DIR'] = tmp_config_dir
        
        self.config['config_dir.working'] = tmp_config_dir
        
        # Persist working config dir accross multiple ConfigLoader instances
        ConfigLoader.SC_CONFIG_INIT_DIR = tmp_config_dir


    def _init_config_dirs(self):
        self._init_default_config_dirs()


    def _init_config(self, config_in):

        self.LOG.debug('_init_config(): config_in: {ci}'.format(ci=config_in))

        self._init_config_dirs()

        working_config_path = os.path.join(
            self.config['config_dir.working'],
            self.SC_CONFIG_FILENAME)


        #
        # Make sure we have a config_in if possible
        #
        
        os_exported_config_in = os.getenv('SC_CONFIG_INIT_IN')
        
        # it is possible for the working config to be reaped by the OS since
        # it is stored in a temporary location - if it has, attempt to
        # recover
        #
        if not os.path.isfile(working_config_path):

            if not config_in and os_exported_config_in:

                self.LOG.debug('working config path not found and no config_in supplied, '\
                    'using saved environment config_in: {ci}'.format(
                        ci=os_exported_config_in))

                config_in = os_exported_config_in


            else:

                self.LOG.debug('initializing empty working config: {}'.format(working_config_path))

                with open(working_config_path, 'w') as wfh:
                    wfh.write(json.dumps({'__bootstrap__': {}}))
        

        # Named config or "default" for default
        #
        if config_in:

            if os.path.isfile(config_in):

                self.LOG.debug('{} -> {}'.format(config_in, working_config_path))
                shutil.copy(config_in, working_config_path)

                self.config['export_env']['SC_CONFIG_INIT_IN'] = os.path.abspath(config_in)

            else:

                user_config_file = 'sc_config_{}.json'.format(config_in)
                user_config_path = os.path.join(
                    self.config['config_dir.user'],
                    user_config_file)

                if os.path.isfile(user_config_path):

                    self.LOG.debug('{} -> {}'.format(user_config_path, working_config_path))
                    shutil.copy(user_config_path, working_config_path)

                    self.config['export_env']['SC_CONFIG_INIT_IN'] = config_in



        build_version = None 
        build_inst_dir = None

        with open(working_config_path) as fh:

            config_dict = json.load(fh)
            if config_dict.get('__bootstrap__') and \
            config_dict['__bootstrap__'].get('build_version'):

                build_version = config_dict['__bootstrap__']['build_version']
                build_inst_dir = config_dict['__bootstrap__'].get('buildsys.inst_dir')

        self.LOG.debug('--= setting build_version: {bv} =--'.format(
            bv=build_version))
        self.LOG.debug('--= setting buildsys.inst_dir: {d} =--'.format(
            d=build_inst_dir))

        self.config['build_version'] = build_version
        self.config['buildsys.inst_dir'] = build_inst_dir


    def post_load_project(self, config_result):

        config = config_result['__bootstrap__']
        if not config.get('project'):
            # self.LOG.warning('No project found in bootstrap!')
            return


        self.LOG.debug('init project')

        project = config['project']

        prompt_tag = config.get('prompt.tag_custom', '')

        config['prompt.tag_custom'] = '{t} | {project}'.format(
            t=prompt_tag,
            project=project)

        config['export_env']['PROJECT'] = project

        scaffold.variant.register_variant(
            'project',
            project,
            scaffold.variant.VARIANT_TYPE_OPTIONAL)


    def post_load(self, config_result):
        self.post_load_project(config_result)


    def load_config(self, config_in):

        if config_in is None:
            config_in = ''

        self._init_config(config_in)

        config_path = self.get_config_path()

        self.LOG.debug('Attempting to load configs: {cp}'.format(cp=config_path))

        config_result = OrderedDict()
        config_result['__bootstrap__'] = copy.deepcopy(self.config)

        for config_entry_dir in reversed(config_path):

            if not config_entry_dir:
                continue

            config_entry_path = os.path.join(config_entry_dir, self.SC_CONFIG_FILENAME)
            if os.path.isfile(config_entry_path):
                with open(config_entry_path) as fh:
                    config_dict = json.load(fh)
                    scaffold.util.deep_merge(config_dict, config_result)

            else:
                self.LOG.error('File not found: {f}'.format(f=config_entry_path))


        self.post_load(config_result)

        return config_result


class BuildConfigLoader(ConfigLoader):

    def _init_build_config_dir(self):
        
        self.LOG.debug('init build config dir')
        
        self.config['config_dir.build'] = None
        
        # import pprint
        # self.LOG.debug(pprint.pformat(self.config))
        
        if 'build_version' not in self.config:
            self.LOG.debug('_init_build_config_dir(): "build_version" not found in config')
            
        if 'buildsys.inst_dir' not in self.config:
            self.LOG.debug('_init_build_config_dir(): "buildsys.inst_dir" not found in config')
            
            
        if self.config.get('build_version'):
            
            build_dir = None
            if self.config.get('buildsys.inst_dir'):
                build_dir = self.config['buildsys.inst_dir']
                
            else:
                # build_flavour, ver_num = self.config['build_version'].split('.')
                build_flavour = '' # self.config['build_version'].split('.')
                parent_build_dir = os.path.join(
                    '/tmp', # self.config['software_dir'],
                    'dist',
                    build_flavour,
                    self.config['build_version'], # could be overriden by user level config
                    'inst')

                build_dir = self._get_platform_dir(parent_build_dir)


            if os.path.isfile(os.path.join(build_dir, self.SC_CONFIG_FILENAME)):
                self.config['config_dir.build'] = build_dir

            else:
                self.LOG.debug('_init_build_config_dir(): config dir {d} not added, no vc config file found'.format(
                    d=build_dir))


    def _init_config_dirs(self):
        ConfigLoader._init_config_dirs(self)
        self._init_build_config_dir()


    def get_config_path(self):

        # Reload this in case it has changed
        self._init_config_dirs()

        config_path = [
            self.config['config_dir.working'],
            self.config['config_dir.build']
        ]

        return config_path


class SingleConfigLoader(ConfigLoader):

    def get_config_path(self):

        # Reload this in case it has changed
        self._init_config_dirs()

        config_path = [
            self.config['config_dir.working'],
        ]

        return config_path


