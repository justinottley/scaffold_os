
import os

from .. import ThirdbaseLib
from ... import util as buildsys_util

class OpenColorIOLib(ThirdbaseLib):
    def _GetOpenColorIODir(self, thirdparty_libs):
        openexr_version = buildsys_util.get_required_thirdparty_version(
            thirdparty_libs, 'OpenColorIO')

        return os.path.join(self.thirdbase_dir, 'OpenColorIO', openexr_version)


    def init(self, benv):
        
        env = benv.env
        
        env['OPENCOLORIODIR'] = self._GetOpenColorIODir(benv.required_thirdparty_libs)

        # For RHEL9 / Rocky 9
        env['GLEWDIR'] = os.path.join(self.thirdbase_dir, 'libGLEW', '2.1.0')

        env['CPPPATH'].insert(0, os.path.join(env['GLEWDIR'], 'include'))
        env['CPPPATH'].insert(0, os.path.join(env['OPENCOLORIODIR'], 'include'))

        for project in ['GLEWDIR', 'OPENCOLORIODIR']:
            for lib_entry in ['lib64', 'lib']:
                project_lib_path = os.path.join(env[project], lib_entry)
                if os.path.isdir(project_lib_path):
                    env['LIBPATH'].insert(0, project_lib_path)


class PosixOpenColorIOLib(OpenColorIOLib):
    def init(self, benv):
        OpenColorIOLib.init(self, benv)

        env = benv.env
        env['LIBS'].extend([
            'GLU',
            'GLEW',
            'OpenColorIO'
        ])


class WindowsOpenColorIOLib(OpenColorIOLib):

    def init(self, benv):
        env = benv.env

        vcpkg_include = os.path.join(self.vcpkg_dir, 'include')
        vcpkg_lib = os.path.join(self.vcpkg_dir, 'debug', 'lib')

        if vcpkg_include not in env['CPPPATH']:
            env['CPPPATH'].insert(0, vcpkg_include)

        if vcpkg_lib not in env['LIBPATH']:
            env['LIBPATH'].insert(0, vcpkg_lib)


        env['LIBS'].extend([
            'freeglutd',
            'glew32d',
            'GLU32',
            'OpenColorIO',
            'OpenColorIOimageioapphelpers',
            'OpenColorIOoglapphelpers'
        ])


PLATFORM_MAP = \
[{'variants':{'opsys':'Linux'},
  'result': PosixOpenColorIOLib},
 {'variants':{'opsys':'Darwin'},
  'result': PosixOpenColorIOLib},
 {'variants':{'opsys':'Windows'},
  'result': WindowsOpenColorIOLib}]
