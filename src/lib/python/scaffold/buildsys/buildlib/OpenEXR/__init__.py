
import os

from .. import ThirdbaseLib
from ... import util as buildsys_util

class OpenEXRLib(ThirdbaseLib):
    
    def _GetOpenEXRDir(self, thirdparty_libs):
        
        openexr_version = buildsys_util.get_required_thirdparty_version(
            thirdparty_libs, 'OpenEXR')
        
        return os.path.join(self.thirdbase_dir, 'OpenEXR', openexr_version)
        
        
    def init(self, benv):

        env = benv.env

        env['OPENEXRDIR'] = self._GetOpenEXRDir(benv.required_thirdparty_libs)

        env['CPPPATH'].insert(0, os.path.join(env['OPENEXRDIR'], 'include'))
        env['CPPPATH'].insert(0, os.path.join(env['OPENEXRDIR'], 'include', 'Imath'))

        for lib_entry in ['lib64', 'lib']:
            lib_path = os.path.join(env['OPENEXRDIR'], lib_entry)
            if os.path.isdir(lib_path):
                env['LIBPATH'].insert(0, lib_path)
                break


class PosixOpenEXRLib(OpenEXRLib):
    def init(self, benv):
        OpenEXRLib.init(self, benv)

        env = benv.env
        '''
        env['LIBS'].extend(['Half',
                            'Imath',
                            'Iex',
                            'IexMath',
                            'IlmThread',
                            'IlmImf'])

        '''
        env['LIBS'].extend([
            'Iex',
            'Imath',
            'IlmThread',
            'OpenEXR',
            'OpenEXRCore',
            'OpenEXRUtil'
        ])

class WindowsOpenEXRLib(OpenEXRLib):

    def _GetOpenEXRDir(self, thirdparty_libs):
        return self.vcpkg_dir

    def init(self, benv):
        env = benv.env

        env['CPPPATH'].insert(0, os.path.join(self.vcpkg_dir, 'include'))
        env['CPPPATH'].insert(0, os.path.join(self.vcpkg_dir, 'include', 'Imath'))
        env['LIBPATH'].insert(0, os.path.join(self.vcpkg_dir, 'debug', 'lib'))

        env['LIBS'].extend([
            'Imath-3_1_d',
            'Iex-3_1_d',
            'IlmThread-3_1_d',
            'OpenEXR-3_1_d',
            'OpenEXRCore-3_1_d',
            'OpenEXRUtil-3_1_d'
        ])


PLATFORM_MAP = \
[{'variants':{'opsys':'Linux'},
  'result': PosixOpenEXRLib},
 {'variants':{'opsys':'Darwin'},
  'result': PosixOpenEXRLib},
 {'variants':{'opsys':'Windows'},
  'result': WindowsOpenEXRLib}]
