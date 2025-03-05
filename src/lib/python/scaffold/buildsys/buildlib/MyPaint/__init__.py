
import os

import scaffold.variant

from .. import ThirdbaseLib
from ... import util as buildsys_util


class MyPaintLib(ThirdbaseLib):

    def _GetMyPaintDir(self, thirdparty_libs):

        libmypaint_version = buildsys_util.get_required_thirdparty_version(
            thirdparty_libs, 'MyPaint')

        if scaffold.variant.get_variant('platform_target') == 'wasm_32':
            libmypaint_version += '_wasm'

        return os.path.join(self.thirdbase_dir, 'libmypaint', libmypaint_version)


    def init(self, benv):

        env = benv.env

        env['MYPAINTDIR'] = self._GetMyPaintDir(benv.required_thirdparty_libs)

        env['CPPPATH'].extend([os.path.join(env['MYPAINTDIR'], 'include')])
        env['LIBPATH'].extend([os.path.join(env['MYPAINTDIR'], 'lib')])

        env['LIBS'].extend(['mypaint'])

        if os.name == 'nt' or scaffold.variant.get_variant('platform_target') == 'wasm_32':
            env['LIBS'].append('json-c')


class IOSMyPaintLib(ThirdbaseLib):

    def _GetMyPaintDir(self, thirdparty_libs):
        root_dir = super(IOSMyPaintLib, self)._GetMyPaintDir(thirdparty_libs)
        return os.path.join(root_dir, 'ios')


PLATFORM_MAP = [
{
    'variants': {'opsys':'Linux'},
    'result': MyPaintLib
},
{
    'variants': {'opsys': 'Windows'},
    'result': MyPaintLib
},
{
    'variants': {'opsys': 'Darwin'},
    'result': MyPaintLib
},
{
    'variants': {'platform_target': 'ios'},
    'result': IOSMyPaintLib
}
]
