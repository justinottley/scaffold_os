#
# Copyright 2014-2024 Justin Ottley
#
# Licensed under the terms set forth in the LICENSE.txt file
#

import os
import sys
import json
import logging
import tempfile
import importlib
from collections import OrderedDict

import scaffold.env
import scaffold.util
import scaffold.variant

from .sset_mgr import SoftwareSetManager

from .sset import SoftwareSet, BuildRelpathSoftwareSet
from .generator import EnvGenerator

class EnvController:

    BOOTSTRAP = '__bootstrap__'

    def __init__(self, config_path=None, config_loader=None, update_current_env=False):

        self.LOG = logging.getLogger('{}.{}'.format(self.__class__.__module__, self.__class__.__name__))

        self.env = None
        self.software_sets = None

        self.config_path = config_path
        self.config_loader = config_loader

        self.update_current_env = update_current_env

        self.env_generator = EnvGenerator.create(self)

        self.initialize()


    @property
    def inst_dir(self):
        return self.config[self.BOOTSTRAP]['buildsys.inst_dir']


    def initialize(self):

        self.LOG.info('initialize()')

        inst_dir = scaffold.util.get_inst_dir()
        scaffold_bin_dir = os.path.join(inst_dir, 'bin')
        scaffold_lib_dir = os.path.join(inst_dir, 'lib', scaffold.variant.get_python_dirname(), 'site-packages')

        self.env = {'PATH':[scaffold_bin_dir],
                    'PYTHONPATH':[scaffold_lib_dir],
                    'LD_LIBRARY_PATH': [],
                    '_USER_PYTHONPATH':[],
                    'SC_PLATFORM': scaffold.variant.get_platform()
                    }

        self.software_sets = OrderedDict()

        self._load_config()
        self._init_base_env()
        self._init_software_sets()
        self._finalize_env()


    def _load_config(self):
        self.config = scaffold.env.load_config(self.config_path, self.config_loader)

        # merge export env from config so that we can add env. variables
        # defined in the config to the resulting exported environment
        #
        self.env.update(self.config[self.BOOTSTRAP].get('export_env', {}))


    def _init_base_env(self):
        
        # set some constants in the current environment for use by path translation
        os.environ['SC_THIRDBASE_VERSION'] = '22_09'
        os.environ['SC_PLATFORM'] = scaffold.variant.get_platform()


        # init a temporary dir for environment files
        sc_temp_dir = os.path.join(tempfile.gettempdir(), os.getenv('USER', os.getenv('USERNAME')), 'scaffold', 'base_environ')
        if not os.path.isdir(sc_temp_dir):
            self.LOG.debug('creating {}'.format(sc_temp_dir))
            os.makedirs(sc_temp_dir)


        # Save a "base" environment file that can be used as a starting point
        # for env. variables that require building
        base_env_file = os.environ.get('SC_ENV_INIT')
        if not base_env_file or not os.path.isfile(base_env_file) or not os.access(base_env_file, os.R_OK):


            # preserve an existing value in PYTHONPATH, and add it to the
            # head of the final pythonpath later.
            # TODO FIXME: This is a bit messy / goofy.. can it be cleaner?
            # if we were using site.py to bootstrap scaffold.vc this might be
            # cleaner
            if os.getenv('_USER_PYTHONPATH'):

                self.LOG.debug('capturing _USER_PYTHONPATH from $_USER_PYTHONPATH: {p}'.format(
                    p=os.environ['_USER_PYTHONPATH']))
                
                self.env['_USER_PYTHONPATH'] = os.environ['_USER_PYTHONPATH'].split(
                    os.pathsep)

            elif os.getenv('PYTHONPATH') and not base_env_file:

                # we can only capture PYTHONPATH if vc has never been turned on
                # in the current shell. Once it is, stash it in _USER_PYTHONPATH
                # since vc will be modifying PYTHONPATH
                
                self.LOG.debug('capturing _USER_PYTHONPATH from $PYTHONPATH: {p}'.format(
                    p=os.environ['PYTHONPATH']))

                os.environ['_USER_PYTHONPATH'] = os.environ['PYTHONPATH']
                
                self.env['_USER_PYTHONPATH'] = os.environ['PYTHONPATH'].split(
                    os.pathsep)

            else:

                self.LOG.debug('PYTHONPATH not found, _USER_PYTHONPATH not found')
                self.env['_USER_PYTHONPATH'] = ['']


            tempfd, base_env_file = tempfile.mkstemp(
                dir=sc_temp_dir,
                prefix='base_environ_',
                suffix='.json')

            os.environ['SC_ENV_INIT'] = base_env_file

            os.write(tempfd, bytes(str(json.dumps(dict(os.environ))), "utf8"))
            os.close(tempfd)

            self.LOG.debug('Wrote base environ: {}'.format(base_env_file))

            # TODO FIXME: the same mechanism as PYTHONPATH above needs to be done
            # with PATH. This is a bug
            #
            self.env['PATH'] = self.env['PATH'] + os.environ['PATH'].split(os.pathsep)


        else:

            self.LOG.debug('initializing base environment from {e}'.format(
                e=os.environ.get('SC_ENV_INIT')))

            # Start the base environment with the original
            #
            with open(os.environ.get('SC_ENV_INIT')) as fh:

                base_env = json.load(fh)
                self.env['_USER_PYTHONPATH'] = base_env.get(
                    '_USER_PYTHONPATH', '').split(os.pathsep)

                self.env['PATH'] = self.env['PATH'] + base_env['PATH'].split(os.pathsep)

        self.env['SC_ENV_INIT'] = base_env_file


    def _init_software_sets(self):

        self.LOG.debug('init_software_sets()')

        self.LOG.debug('')

        if 'sclib' not in self.config:
            # self._init_builtin_sclib_setup()
            raise Exception('sclib default setup not implemented yet')


        sset_mgr = SoftwareSetManager(self.config, self.config_path)
        self.software_sets = sset_mgr._software_sets

        for sset_obj in self.software_sets.values():
            sset_obj.on_init(self.env)


        '''
        #
        # sclib software set is force created to update sys.path so the subsequent
        # sclib classes can be imported
        #
        #
        
        # NOTE that the sclib SoftwareSet will be initialized again a second time
        # in the below software set loop likely with a different class - this is just for updating sys.path
        sclib_sset = BuildRelpathSoftwareSet(self, 'sclib', self.config['sclib'])

        if sys.path[0] != sclib_sset.python_lib_dir and os.path.isdir(sclib_sset.python_lib_dir):
            self.LOG.debug('Inserting into PYTHONPATH for sclib access: {p}'.format(p=sclib_sset.python_lib_dir))
            sys.path.insert(0, sclib_sset.python_lib_dir)

        try:
            import sclib
            importlib.reload(sclib)

            self.LOG.debug(sclib)
            self.LOG.debug('')

        except Exception as e:
            self.LOG.debug('could not import sclib: {en}: {e}'.format(en=e.__class__.__name__, e=e))


        for software_set_name in self.config.keys():
            
            if software_set_name in ['__bootstrap__']:
                continue


            self.LOG.debug('initializing {}'.format(software_set_name))

            # Use a predefined software set subclass if it exists,
            # otherwise use the base Package class
            #
            sftset_cls = SoftwareSet
            if 'sclib.cls' in self.config[software_set_name]:
                sftset_cls = scaffold.util.import_object(
                    self.config[software_set_name]['sclib.cls'])


            # instantiate
            sset_obj = sftset_cls(self, software_set_name, self.config[software_set_name])

            # build base environment based on the executing platform. Check
            # to ensure the package supports the platform / variant specified
            # in the package
            if scaffold.variant.match_any(sset_obj.variants):

                # build base environment
                # self._build_base_env(package)
                self.LOG.debug('calling on_init() for {}'.format(sset_obj))

                # run package callback
                sset_obj.on_init(self.env)

                self.software_sets[software_set_name] = sset_obj

            else:

                self.LOG.debug('skipping init, no matching variants for {}'.format(software_set_name))
        '''
        


    def _finalize_env(self):
        '''
        Perform any final modifications to the environment after loading
        everything
        '''

        self.LOG.debug('finalizing environment')
        self.LOG.debug('user pythonpath: {user_ppath}'.format(
            user_ppath=self.env['_USER_PYTHONPATH']))

        self.LOG.debug('pythonpath: {ppath}'.format(ppath=self.env['PYTHONPATH']))
        
        # add user PYTHONPATH to the front of PYTHONPATH
        self.env['PYTHONPATH'] = self.env['_USER_PYTHONPATH'] + \
                                 self.env['PYTHONPATH']

        # add scaffold bin dir to PATH

        # Set config loader to single so that we reuse the 
        # setup working config (that can potentially be changed)
        self.env['SC_CONFIG_LOADER'] = 'Single'

        # NOTE: clients may want the environment of the current
        # process updated to reflect the environment generated - 
        # the following call updates the environment of the
        # current process

        if self.update_current_env:
            self.env_generator.update_env()


    def generate_env_file(self, *args, **kwargs):
        return self.env_generator.generate_env_file(*args, **kwargs)
