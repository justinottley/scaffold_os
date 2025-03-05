#
# Copyright 2014-2024 Justin Ottley
#
# Licensed under the terms set forth in the LICENSE.txt file
#

import os
import json
import pprint
import logging

import scaffold.variant

from .. import util as scaffold_util

class SoftwareSet:

    PLATFORM_LINUX = [{'opsys':'Linux'}]
    PLATFORM_WINDOWS = [{'opsys':'Windows'}]
    PLATFORM_DARWIN = [{'opsys':'Darwin'}]

    PLATFORM_ALL = PLATFORM_LINUX + \
                   PLATFORM_WINDOWS + \
                   PLATFORM_DARWIN

    def __init__(self, cntrl, name, sset_config):
        self.LOG = logging.getLogger('{}.{}'.format(self.__class__.__module__, self.__class__.__name__))

        self._cntrl = cntrl
        self.__name = name
        self.config = sset_config


    @property
    def cntrl(self):
        return self._cntrl

    @property
    def variants(self):
        return self.PLATFORM_ALL

    @property
    def name(self):
        return self.__name

    @property
    def sftset_name(self):
        return self.__name

    @property
    def sftset_version(self):
        return self.config.get('sftset_version', '')

    @property
    def sftset_type(self):
        return self.config['sftset_type']

    @property
    def release_num_str(self):
        return str(self.config['release_num']).zfill(4)

    @property
    def project_name(self):
        return self.cntrl.project_name


    @property
    def base_uri(self):
        return 'dist://proj/{}/sset/{}/{}/{}'.format(
            self.config.get('sftset_project', self.project_name),
            self.name,
            self.config['sftset_version'],
            self.release_num_str
        )

    @property
    def done_uri(self):
        return '{}/.done'.format(self.base_uri)


    @property
    def zip_uri(self):
        return 'dist://proj/{}/sset/{}/{}/sset_{}_{}_{}.7z'.format(
            self.config.get('sftset_project', self.project_name),
            self.name,
            self.config['sftset_version'],
            self.name,
            self.config['sftset_version'],
            self.release_num_str
        )


    @property
    def base_dir(self):
        '''
        Implement in subclass
        '''
        return None


    @property
    def bin_dir(self):
        return os.path.join(
            self.base_dir, 'bin'
        )


    @property
    def lib_dir(self):
        return os.path.join(self.base_dir, 'lib')


    @property
    def python_lib_dir(self):
        return os.path.join(
            self.base_dir,
            'lib',
            scaffold.variant.get_python_dirname(),
            'site-packages'
        )


    def on_init_pth(self, env):

        py_path_contents = os.listdir(self.python_lib_dir)
        for py_entry in py_path_contents:
            if py_entry.endswith('.pth'):

                pth_file_path = os.path.join(self.python_lib_dir, py_entry)
                self.LOG.debug('{}: Found .pth file: {}'.format(
                    self.name, pth_file_path))

                with open(pth_file_path) as fh:
                    for py_lib_line in fh.readlines():
                        py_lib_line = py_lib_line.strip()
                        if not py_lib_line or py_lib_line.startswith('#') or '.egg' not in py_lib_line:
                            continue

                        pth_lib_path = os.path.join(self.python_lib_dir, py_lib_line)

                        self.LOG.debug('{}: Inserting into PYTHONPATH: {}'.format(
                            self.name, pth_lib_path))

                        env['PYTHONPATH'].insert(0, pth_lib_path)


    def on_init(self, env):

        if not self.base_dir:
            self.LOG.error('{} - No base_dir, returning'.format(self.name))
            return

        _bin_dir = self.bin_dir
        if os.path.isdir(_bin_dir):
            env['PATH'].insert(0, _bin_dir)

        else:
            self.LOG.debug('PATH - Skipping, not found: {}'.format(_bin_dir))


        self.LOG.debug('{} - CHECKING pylib dir: {}'.format(self.name, self.python_lib_dir))
        if os.path.isdir(self.python_lib_dir):
            env['PYTHONPATH'].insert(0, self.python_lib_dir)
            self.on_init_pth(env)

        self.LOG.debug('{} - CHECKING  {}'.format(self.name, self.lib_dir))
        if os.path.isdir(os.path.join(self.lib_dir)):
            if os.name == 'nt':
                env['PATH'].insert(0, self.lib_dir)

            else:
                env['LD_LIBRARY_PATH'].insert(0, self.lib_dir)


    def has_release(self):
        return 'release_num' in self.config


    def set_release_num(self, release_num):
        self.config['release_num'] = release_num


    def is_install_required(self):
        from scaffold.ext.path import Path
        sc_sset_done_path = Path(self.done_uri).format(translation_map='local')

        print(sc_sset_done_path)
        print('')
        return not os.path.isfile(sc_sset_done_path)


    def get_install_required(self, include_types=None, exclude_types=None):

        if self.is_install_required():
            return [self]

        return []


    def get_all(self):
        return [self]


class ExternalSoftwareSet(SoftwareSet):

    def __init__(self, *args, **kwargs):
        SoftwareSet.__init__(self, *args, **kwargs)

        from scaffold.ext.path import Path

        self._base_dir = str(Path('dist://'))


    @property
    def base_dir(self):

        from scaffold.ext.path import Path

        if self.config.get('release_num'):
            base_dir = Path('dist://').format(translation_map='local')

            return os.path.join(
                base_dir,
                'proj',
                self.config['sftset_project'],
                'sset',
                self.name,
                self.config['sftset_version'],
                self.release_num_str
            )

        return os.path.join(self._base_dir, self.name)



class BuildRelpathSoftwareSet(SoftwareSet):

    @property
    def base_dir(self):

        if self.cntrl.config_path:
            return os.path.join(
                os.path.dirname(os.path.realpath(self.cntrl.config_path)),
                self.name)

        else:
            # init without a config
            scaffold_root_dir = os.path.dirname(
                os.path.dirname(os.path.realpath(__file__)))

            return os.path.join(scaffold_root_dir, 'ext', self.name)


class SclibSoftwareSet(BuildRelpathSoftwareSet):

    def __init__(self, *args, **kwargs):
        BuildRelpathSoftwareSet.__init__(self, *args, **kwargs)

        self.tr_path_list = [] # setup in init_translation_map()
        self._local_base_dir = None

        for export_key, export_val in self.config.get('export_env', {}).items():
            os.environ[export_key] = export_val

        self._base_dir = None
        self._init()


    @property
    def local_dist_dir(self):
        '''
        Kinda needed since path translation may not be available yet
        when the Software Set Manager is trying to find the python lib dir for sclib
        '''
        return os.path.join(os.path.expanduser('~'), '.config', 'rlp', os.getenv('RLP_SITE'), 'release', os.getenv('SC_PLATFORM'), 'dist')


    @property
    def base_dir(self):
        return self._base_dir


    @property
    def python_lib_dir(self):
        if self.cntrl.config_path:
            return super().python_lib_dir

        return self.base_dir


    @property
    def sclib_dir(self):
        return os.path.dirname(self.cntrl.sclib_module.__file__)


    def _init(self):

        if self.cntrl.config_path:

            if self.config.get('release_num'):
                
                self._base_dir = '{}/proj/{}/sset/{}/{}/{}'.format(
                    self.local_dist_dir,
                    self.cntrl.config_bootstrap['project'],
                    self.name,
                    self.config['sftset_version'],
                    str(self.config['release_num']).zfill(4)
                )

            else:

                # dev environment won't have a release_num
                self._base_dir = os.path.join(
                    os.path.dirname(os.path.realpath(self.cntrl.config_path)),
                    self.name)

        else:
            # init without a config.. use scaffold built-in sclib
            #
            scaffold_root_dir = os.path.dirname(
                os.path.dirname(os.path.realpath(__file__)))

            self._base_dir = os.path.join(scaffold_root_dir, 'ext')

            # this is expected in the build config. Since we don't 
            # have one, force dev
            self.config['translation_map'] = ['dev']


    def _init_translation_map(self):
        '''
        Called from SoftwareSet Manager in _init_software_sets()
        '''

        # attempt to startup path translation mapping

        self.LOG.info('sclib dir: {}'.format(self.sclib_dir))
        self.LOG.info('translation config list: {}'.format(self.config['translation_map']))

        tr_path_list = []
        for tr_entry in self.config['translation_map']:
            tr_path_list.append(os.path.join(self.sclib_dir, 'translation_config', tr_entry))

        # Late import required, but not sure why?
        import scaffold.variant
        
        # for other SoftwareSet classes
        sc_tr_map_path = os.pathsep.join(tr_path_list)
        os.environ['SC_TRANSLATION_MAP_PATH'] = sc_tr_map_path

        self.LOG.info('SC_TRANSLATION_MAP_PATH={}'.format(sc_tr_map_path))


        # initialize path translation
        import scaffold.ext.path


    def on_init(self, env):

        tr_path_list = []
        for tr_entry in self.config['translation_map']:
            tr_path_list.append(os.path.join(self.sclib_dir, 'translation_config', tr_entry))

        env['SC_TRANSLATION_MAP_PATH'] = tr_path_list

        for export_key, export_val in self.config.get('export_env', {}).items():
            env[export_key] = export_val


class AppSoftwareSet(SoftwareSet):

    @property
    def release_num_str(self):
        return ''

    @property
    def base_uri(self):
        return 'apps://{}/{}'.format(
            self.name,
            self.config['sftset_version']
        )

    @property
    def zip_uri(self):
        return 'apps://{}/{}.7z'.format(
            self.name,
            self.config['sftset_version'])

    @property
    def base_dir(self):
        from scaffold.ext.path import Path
        return str(Path(self.base_uri))


    def has_release(self):
        return True


class ThirdbaseProject(SoftwareSet):

    @property
    def base_dir(self):
        return os.path.join(
            self.cntrl._base_dir,
            self.config['name'],
            self.sftset_version
        )

    @property
    def release_num_str(self):
        return ''

    @property
    def sftset_type(self):
        return 'tb_project'

    @property
    def sftset_version(self):
        if 'version.map' in self.config:
            plat = scaffold.variant.get_platform()
            if plat in self.config['version.map']:
                return self.config['version.map'][plat]

        return self.config['version']


    @property
    def base_uri(self):
        return 'thirdbase://{}/{}'.format(
            self.config['name'],
            self.sftset_version
        )

    @property
    def zip_uri(self):
        return 'thirdbase://{}/{}.7z'.format(
            self.config['name'],
            self.sftset_version
        )


    def has_release(self):
        return True


class ThirdbaseSoftwareSet(SoftwareSet):

    def __init__(self, *args, **kwargs):
        SoftwareSet.__init__(self, *args, **kwargs)

        # NOTE: late import
        from scaffold.ext.path import Path
        self._base_dir = str(Path('thirdbase://'))

        self._projects = []
        self._init_projects()


    @property
    def base_dir(self):
        return self._base_dir


    def has_release(self):
        return True


    def _init_projects(self):

        self.LOG.debug(pprint.pformat(self.config))
        for tb_project in self.config['flavour']['default']:
            
            if 'variants' in tb_project:
                if not scaffold.variant.match_any(tb_project['variants']):
                    self.LOG.debug('No scaffold.variant matches, skipping: {}'.format(
                        tb_project['name']
                    ))
                    continue
    
            tb_cls = ThirdbaseProject
            if 'sclib.cls' in tb_project:
                tb_cls = sftset_cls = scaffold_util.import_object(tb_project['sclib.cls'])

            tb_proj_obj = tb_cls(self, tb_project['name'], tb_project)
            self._projects.append(tb_proj_obj)


    def on_init(self, env):

        env['SC_THIRDBASE_VERSION'] = self.config['sftset_version']

        for tb_proj in self._projects:

            self.LOG.debug('{} - {}'.format(tb_proj.name, tb_proj))
            tb_proj.on_init(env)


        return


        for tb_entry in self.config['flavour']['default']:
            proj_dir = os.path.join(self.base_dir, tb_entry['name'], tb_entry['version'])

            if not os.path.isdir(proj_dir):
                self.LOG.debug('NOT FOUND: {}'.format(proj_dir))
                continue

            
            proj_bin_dir = os.path.join(proj_dir, 'bin')
            if os.path.isdir(proj_bin_dir):
                self.LOG.debug('adding to PATH: {}'.format(proj_bin_dir))
                env['PATH'].insert(0, proj_bin_dir)


            proj_lib_dir = os.path.join(proj_dir, 'lib')
            if os.path.isdir(proj_lib_dir):
                self.LOG.debug('adding to LD_LIBRARY_PATH: {}'.format(proj_lib_dir))
                env['LD_LIBRARY_PATH'].insert(0, proj_lib_dir)


            proj_pylib_dir = os.path.join(proj_lib_dir, scaffold.variant.get_python_dirname(), 'site-packages')
            if os.path.isdir(proj_pylib_dir):
                self.LOG.debug('adding to PYTHONPATH: {}'.format(proj_pylib_dir))
                env['PYTHONPATH'].insert(0, proj_pylib_dir)


                py_path_contents = os.listdir(proj_pylib_dir)
                for py_entry in py_path_contents:
                    if py_entry.endswith('.pth'):

                        pth_file_path = os.path.join(proj_pylib_dir, py_entry)
                        self.LOG.debug('{}: Found .pth file: {}'.format(
                            tb_entry['name'], pth_file_path))

                        with open(pth_file_path) as fh:
                            for py_lib_line in fh.readlines():
                                py_lib_line = py_lib_line.strip()
                                if not py_lib_line or py_lib_line.startswith('#'):
                                    continue

                                pth_lib_path = os.path.join(proj_pylib_dir, py_lib_line)
    
                                self.LOG.debug('{}: Inserting into PYTHONPATH: {}'.format(
                                    tb_entry['name'], pth_lib_path))

                                env['PYTHONPATH'].insert(0, pth_lib_path)


            else:
                self.LOG.debug('NOT FOUND: {}'.format(proj_pylib_dir))


    def is_install_required(self):

        for tb_proj in self._projects:
            if tb_proj.is_install_required():
                return True

        return False


    def get_install_required(self, *args, **kwargs):

        result = []
        for tb_proj in self._projects:
            if tb_proj.is_install_required():
                result.append(tb_proj)

        return result


    def get_all(self):
        return self._projects


class BuildSoftwareSet(SoftwareSet):

    def __init__(self, *args, **kwargs):
        SoftwareSet.__init__(self, *args, **kwargs)

        self._ssets = []

        try:
            pass
            self._init_build()
        except:
            pass


    @property
    def project_name(self):
        return self.cntrl['sftset_project']


    def _init_build(self):

        self.LOG.info('')


        from rlp.core.net.websocket import RlpClient
        edbc = RlpClient.instance()

        def _sset_info_ready(result):

            for entry in result:
                sset_name = entry['sset_name']
                entry_config = json.loads(entry['sset_config'])

                sset_obj = self.cntrl._init_sset_obj(sset_name, entry_config)

                # redirect the softwareset cntrl to ensure it has a valid project
                sset_obj._cntrl = self
                self._ssets.append(sset_obj)


        def _build_sset_ready(result):

            sset_uuids = []
            for entry in result:
                if 'sset_release' not in entry:
                    self.LOG.error('No linked SoftwareSetRelease - {}'.format(entry))
                    continue

                sset_uuids.append('{' + entry['sset_release']['uuid'] + '}')

            edbc.call(_sset_info_ready, 'edbc.find', 'SoftwareSetRelease',
                [
                    ['uuid', 'in', sset_uuids]
                ],
                ['sset_name', 'sset_config', 'sset_release_num']
            ).run()
                

        def _build_info_ready(result):

            if len(result) != 1:
                # maybe the connected build hasn't been released?
                self.LOG.error('Invalid BuildVersion for project: {} build_version: {}'.format(
                    self.config['sftset_project'], self.config['sftset_version']
                ))
                self.LOG.error('Got {} results'.format(len(result)))
                return

            edbc.call(_build_sset_ready, 'edbc.find', 'BuildSoftwareSet',
                [
                    ['build_version', 'is', result[0]]
                ],
                ['sset_release', 'sset_name']
            ).run()


        def _project_ready(result):
            assert(len(result) == 1)

            edbc.call(_build_info_ready, 'edbc.find', 'BuildVersion',
                [
                    ['project', 'is', result[0]],
                    ['version', 'is', self.config['sftset_version']]
                ],
                []
            ).run()


        edbc.call(_project_ready, 'edbc.find', 'Project',
            [
                ['name', 'is', self.config['sftset_project']]
            ],
            []
        ).run()



    def is_install_required(self):

        for sset in self._ssets:
            if sset.is_install_required():
                return True

        return False


    def get_install_required(self, *args, **kwargs):
        result = []
        for sset in self._ssets:
            result.extend(sset.get_install_required(*args, **kwargs))

        return result


    def get_all(self):
        result = []
        for sset in self._ssets:
            result.extend(sset.get_all())

        return result


class QtSoftwareSet(ThirdbaseProject):

    @property
    def plat_prefix(self):
        _plat_prefix = 'gcc_64'
        if os.name == 'nt':
            _plat_prefix = 'msvc2019_64'

        return _plat_prefix


    @property
    def bin_dir(self):
        return os.path.join(self.base_dir, self.plat_prefix, 'bin')

    @property
    def lib_dir(self):
        return os.path.join(self.base_dir, self.plat_prefix, 'lib')

