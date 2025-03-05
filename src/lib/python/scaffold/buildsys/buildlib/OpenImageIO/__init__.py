
import os

from .. import ThirdbaseLib
from ... import util as buildsys_util

class OpenImageIOLib(ThirdbaseLib):
    
    def _GetOpenImageIODir(self, thirdparty_libs):
        
        openexr_version = buildsys_util.get_required_thirdparty_version(
            thirdparty_libs, 'OpenImageIO')
        
        return os.path.join(self.thirdbase_dir, 'OpenImageIO', openexr_version)
        
        
    def init(self, benv):
        
        env = benv.env
        
        env['OPENIMAGEIODIR'] = self._GetOpenImageIODir(benv.required_thirdparty_libs)

        env['CPPPATH'].insert(0, os.path.join(env['OPENIMAGEIODIR'], 'include'))

        for project in ['OPENIMAGEIODIR']:
            for lib_entry in ['lib64', 'lib']:
                project_lib_path = os.path.join(env[project], lib_entry)
                if os.path.isdir(project_lib_path):
                    env['LIBPATH'].insert(0, project_lib_path)
                    break


class PosixOpenImageIOLib(OpenImageIOLib):
    def init(self, benv):
        OpenImageIOLib.init(self, benv)

        env = benv.env
        env['LIBS'].extend([
            'OpenImageIO',
            'OpenImageIO_Util'
        ])


class WindowsOpenImageIOLib(OpenImageIOLib):

    def init(self, benv):
        env = benv.env

        vcpkg_include = os.path.join(self.vcpkg_dir, 'include')
        vcpkg_lib = os.path.join(self.vcpkg_dir, 'debug', 'lib')

        if vcpkg_include not in env['CPPPATH']:
            env['CPPPATH'].insert(0, vcpkg_include)

        if vcpkg_lib not in env['LIBPATH']:
            env['LIBPATH'].insert(0, vcpkg_lib)

        env['LIBS'].extend([
            'boost_atomic-vc140-mt-gd',
            'boost_chrono-vc140-mt-gd',
            'boost_container-vc140-mt-gd',
            'boost_context-vc140-mt-gd',
            'boost_coroutine-vc140-mt-gd',
            'boost_date_time-vc140-mt-gd',
            'boost_exception-vc140-mt-gd',
            'boost_filesystem-vc140-mt-gd',
            'boost_random-vc140-mt-gd',
            'boost_regex-vc140-mt-gd',
            'boost_stacktrace_noop-vc140-mt-gd',
            'boost_stacktrace_windbg-vc140-mt-gd',
            'boost_stacktrace_windbg_cached-vc140-mt-gd',
            'boost_system-vc140-mt-gd',
            'boost_thread-vc140-mt-gd',
            'fmtd',
            'freeglutd',
            'glew32d',
            'GLU32',
            'jpeg',
            'libpng16d',
            'lzma',
            'tiffd',
            'turbojpeg',
            'zlibd',
            'Imath-3_1_d',
            'Iex-3_1_d',
            'IlmThread-3_1_d',
            'OpenEXR-3_1_d',
            'OpenEXRCore-3_1_d',
            'OpenEXRUtil-3_1_d',
            'OpenGL32',
            'OpenImageIO_d',
            'OpenImageIO_Util_d'
        ])


PLATFORM_MAP = \
[{'variants':{'opsys':'Linux'},
  'result': PosixOpenImageIOLib},
 {'variants':{'opsys':'Darwin'},
  'result': PosixOpenImageIOLib},
 {'variants':{'opsys':'Windows'},
  'result': WindowsOpenImageIOLib}]
