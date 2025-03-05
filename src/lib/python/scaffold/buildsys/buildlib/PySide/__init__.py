
import os
import sys
import platform

import scaffold.variant
import scaffold.buildsys

from .. import ThirdbaseLib

pyver_parts = platform.python_version_tuple()
PYVER = 'python{}.{}'.format(pyver_parts[0], pyver_parts[1])

class PySideLib(ThirdbaseLib):

    def _GetPySideDir(self, thirdparty_libs):

        sbk_version = scaffold.buildsys.util.get_required_thirdparty_version(
            thirdparty_libs, 'PySide')

        return os.path.join(self.thirdbase_dir, 'PySide6', sbk_version)


    def init(self, benv):
        ThirdbaseLib.init(self, benv)

        env = benv.env
        env['SBKDIR'] = self._GetPySideDir(benv.required_thirdparty_libs)

        # pyside_sp_dir = os.path.join(env['SBKDIR'], 'lib', pydirname, 'site-packages')


class LinuxPySideLib(PySideLib):

    def init(self, benv):
        PySideLib.init(self, benv)

        env = benv.env

        qtdir = env['DIR.QT']
        pyside_dir = env['SBKDIR']
        pyside_sp_dir = os.path.join(env['SBKDIR'], 'lib', PYVER, 'site-packages')

        env['CPPPATH'].extend([
            os.path.join(pyside_sp_dir, 'shiboken6_generator', 'include'),
            os.path.join(pyside_sp_dir, 'PySide6', 'include', 'shiboken6'),
            os.path.join(pyside_sp_dir, 'PySide6', 'include'),
            os.path.join(pyside_sp_dir, 'PySide6', 'include', 'QtCore'),
            os.path.join(pyside_sp_dir, 'PySide6', 'include', 'QtGui'),
            os.path.join(pyside_sp_dir, 'PySide6', 'include', 'QtWidgets'),
            os.path.join(qtdir, 'include', 'QtCore'),
            os.path.join(qtdir, 'include', 'QtGui'),
            os.path.join(qtdir, 'include', 'QtWidgets'),
            os.path.join(qtdir, 'include', 'QtOpenGLWidgets'),
            os.path.join(qtdir, 'include', 'QtOpenGL')
        ])

        env['LIBPATH'].extend([
            os.path.join(env['SBKDIR'], 'lib')
        ])

        env['LIBS'].extend([
            'shiboken6',
            'pyside6'
        ])



PLATFORM_MAP = \
[{'variants':{'opsys':'Linux'},
  'result':LinuxPySideLib},
]