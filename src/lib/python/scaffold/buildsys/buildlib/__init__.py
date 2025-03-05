
import os
import logging

import scaffold.variant


from .. import util as buildsys_util
from .. import globals as buildsys_globals

LIBS = {}

class Builder(object):

    def __init__(self, benv, deps=None):
        self.LOG = logging.getLogger('{}.{}'.format(self.__class__.__module__, self.__class__.__name__))

        self.benv = benv
        self.deps = deps or []


    @property
    def outputs(self):
        return []


    def _get_relpath(self, file_fullpath):
        file_relpath = file_fullpath.replace(self.benv.root_dir, '')
        if file_relpath.startswith(os.path.sep):
            file_relpath = file_relpath[1:]

        return file_relpath


    def gen_rules(self):
        return ''


    def to_ninja(self):
        raise NotImplementedError


class BuildlibBase(object):

    BUILDERS = {}

    def __init__(self):
        self.LOG = logging.getLogger('{}.{}'.format(
            self.__class__.__module__, self.__class__.__name__))

    def builder(self, name):
        return self.BUILDERS[name]


class ThirdbaseLib(BuildlibBase):

    @property
    def thirdbase_dir(self):

        tb_dir = buildsys_globals.senv_config['dir.thirdbase']
        return tb_dir

        # check for minor version first, then use major version if minor not found
        # platform_minor_dir = os.path.join(tb_dir, scaffold.variant.get_platform(minor=True))
        # platform_major_dir = os.path.join(tb_dir, scaffold.variant.get_platform())
        # 
        # if os.path.isdir(platform_minor_dir):
        #     return platform_minor_dir
        # 
        # return platform_major_dir

    @property
    def vcpkg_dir(self):
        return os.path.join(self.thirdbase_dir, 'vcpkg', 'vcpkg', 'installed', 'x64-windows')

    def init(self, benv):
        pass


def get_lib(name):

    if name in LIBS:
        return LIBS[name]

    lib_ns = '{}.{}'.format(__name__, name)
    lib_mod = buildsys_util.import_module(lib_ns)

    module_cls = scaffold.variant.match_result(lib_mod.PLATFORM_MAP)
    if module_cls:
        module_obj = module_cls()
        module_cls._instance = module_obj
        LIBS[name] = module_obj

        return module_obj

