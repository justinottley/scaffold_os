
import os

from .. import ThirdbaseLib

from ... import util as buildsys_util


class LinuxFuseLib(ThirdbaseLib):

    def _GetFuseDir(self, thirdparty_libs):

        fuse_version = buildsys_util.get_required_thirdparty_version(
            thirdparty_libs, 'Fuse')

        return os.path.join(self.thirdbase_dir, 'libfuse', fuse_version)


    def init(self, benv):

        env = benv.env

        env['FUSEDIR'] = self._GetFuseDir(benv.required_thirdparty_libs)

        env['CPPPATH'].extend([os.path.join(env['FUSEDIR'], 'include')])
        env['LIBPATH'].extend([
            os.path.join(env['FUSEDIR'], 'lib', 'x86_64-linux-gnu')
        ])

        # env['RPATH'].extend(env['LIBPATH'])
        env['LIBS'].extend(['fuse3'])


class DarwinFuseLib(ThirdbaseLib):

    def _GetFuseDir(self, thirdparty_libs):
        return '/usr/local'


    def init(self, benv):
        
        env = benv.env
        
        env['FUSEDIR'] = self._GetFuseDir(benv.required_thirdparty_libs)
        
        env['CPPPATH'].extend([os.path.join(env['FUSEDIR'], 'include')])
        env['LIBPATH'].extend([
            os.path.join(env['FUSEDIR'], 'lib')
        ])
    
        env['RPATH'].extend(env['LIBPATH'])
        env['LIBS'].extend(['fuse'])

        env['CPPDEFINES'].extend(['_FILE_OFFSET_BITS=64', '_DARWIN_USE_64_BIT_INODE'])



class WindowsFuseLib(ThirdbaseLib):

    def _GetFuseDir(self, thirdparty_libs):

        fuse_version = '2022'
        return os.path.join(self.thirdbase_dir, 'WinFsp', fuse_version)

    def init(self, benv):
        
        env = benv.env
        
        env['FUSEDIR'] = self._GetFuseDir(benv.required_thirdparty_libs)
        
        env['CPPPATH'].extend([os.path.join(env['FUSEDIR'], 'inc')])
        env['LIBPATH'].extend([
            os.path.join(env['FUSEDIR'], 'lib')
        ])

        env['RPATH'].extend(env['LIBPATH'])
        env['LIBS'].extend(['winfsp-x64'])


PLATFORM_MAP = \
[
    {'variants':{'opsys':'Linux'}, 'result':LinuxFuseLib},
    {'variants':{'opsys':'Windows'}, 'result':WindowsFuseLib},
    {'variants':{'opsys':'Darwin'}, 'result':DarwinFuseLib}
]
