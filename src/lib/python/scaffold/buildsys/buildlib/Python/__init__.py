


import os

from .. import ThirdbaseLib

from ... import util as buildsys_util


class LinuxPythonLib(ThirdbaseLib):

    BUILDERS = {}

    def _GetPythonDir(self, thirdparty_libs):

        python_version = buildsys_util.get_required_thirdparty_version(
            thirdparty_libs, 'Python')

        base_dir = os.path.join(self.thirdbase_dir, 'python', python_version)

        return (base_dir, python_version)

    def init(self, benv):

        base_dir, python_version = self._GetPythonDir(benv.required_thirdparty_libs)

        env = benv.env

        env['PYTHONDIR'] = base_dir

        # python3-config --includes
        env['CPPPATH'].extend([
            '{}/include/python{}'.format(base_dir, python_version)
        ])

        env['LIBPATH'].extend([
            '{}/lib'.format(base_dir)
        ])

        env['LIBS'].extend([
                'python{}'.format(python_version),
                # 'crypt',
                # 'pthread',
                'dl',
                # 'util',
                'm'
            ])



class DarwinPythonLib(LinuxPythonLib):
    
    def init(self, benv):

        env = benv.env

        base_dir, python_version = self._GetPythonDir(benv.required_thirdparty_libs)

        pydir = 'python{}'.format(python_version)

        # via python3-config
        #
        # -L/Library/Frameworks/Python.framework/Versions/3.7/lib/python3.7/config-3.7m-darwin -lpython3.7m -ldl -framework CoreFoundation

        env['CPPPATH'].extend([
            '/Library/Frameworks/Python.framework/Versions/{}/include/{}'.format(python_version, pydir)
        ])
        env['LIBPATH'].extend([
            '/Library/Frameworks/Python.framework/Versions/{}/lib'.format(
                python_version),
            # '/Library/Frameworks/Python.framework/Versions/{}/lib/{}/config-{}-darwin'.format(
            #     python_version, python_version, python_version)
        ])

        env['LIBS'].extend([
            pydir,
            'dl'
        ])

        env['FRAMEWORKS'].extend(['CoreFoundation'])


class IOSPythonLib(ThirdbaseLib):

    def _GetPythonDir(self, thirdparty_libs):

        python_version = buildsys_util.get_required_thirdparty_version(
            thirdparty_libs, 'Python')

        base_dir = os.path.join(self.thirdbase_dir, 'python', 'ios')

        return (base_dir, python_version)

    def init(self, benv):

        base_dir, python_version = self._GetPythonDir(benv.required_thirdparty_libs)
        python_dirname = 'python{}'.format(python_version)

        env = benv.env

        env['CPPPATH'].append(
            os.path.join(base_dir, 'Python.xcframework/ios-arm64/include/{}'.format(python_dirname))
        )

        env['FRAMEWORKPATH'].append(
            os.path.join(base_dir, 'Python.xcframework/ios-arm64')
        )

        env['FRAMEWORKS'].append('Python')


class WasmPythonLib(ThirdbaseLib):
    def _GetPythonDir(self, thirdparty_libs):

        python_version = buildsys_util.get_required_thirdparty_version(
            thirdparty_libs, 'Python')

        python_version += '_wasm'

        # base_dir = os.path.join(self.thirdbase_inst_dir, 'python', 'cpython_3.11_wasm', 'builddir', 'emscripten-browser', 'usr')
        base_dir = os.path.join(self.thirdbase_dir, 'python', python_version)
        return (python_version, base_dir)


    def init(self, benv):

        env = benv.env
        python_version, base_dir = self._GetPythonDir(benv.required_thirdparty_libs)

        python_dirname = 'python{}'.format(python_version.replace('_wasm', ''))

        env['PYTHONDIR'] = base_dir
        

        env['CPPPATH'].extend([
            os.path.join(env['PYTHONDIR'],
            'include',
            python_dirname)
        ])


        for lib_entry in [
            'libmpdec.a',
            'libexpat.a',
            'libHacl_Hash_SHA2.a',
            'lib{}.a'.format(python_dirname)
        ]:
            env['LINKFLAGS'].append(
                os.path.join(env['PYTHONDIR'], 'lib', lib_entry)
            )

        # WARNING: Qt 6.7 seems to have broken the --preload-file option
        # https://forum.qt.io/topic/151022/qt-6-6-application-exit-module-prerun-push-is-not-a-function
        #
        preload_path = os.path.join(env['PYTHONDIR'], 'preload')
    
        env['LINKFLAGS'].extend([
            '-sWASM_BIGINT',
            '-sUSE_BZIP2',
            '-sUSE_SQLITE3',
            '-sUSE_ZLIB',
            '--preload-file', '{}@lib'.format(preload_path),
            # '--preload-file', '/home/justinottley/dev/revlens_root/thirdbase/22_09/Linux-x86_64/python/cpython_3.11_wasm/builddir/emscripten-browser/usr/local/lib@lib',
            '--preload-file', '/home/justinottley/dev/revlens_root/sp_revsix/wasm_fs_root@wasm_fs_root'
        ])

        # env.Append(LINKFLAGS=[
        #     '-s', 'EMULATE_FUNCTION_POINTER_CASTS=1',
        #    '--memory-init-file', '0',
        #    '--preload-file', '/home/justinottley/dev/revlens_root/thirdbase/22_09/Linux-x86_64/python/3.7.14_wasm/lib@lib'
        # ])


class WindowsPythonLib(ThirdbaseLib):
    
    def _GetPythonDir(self, thirdparty_libs):
        
        python_version = buildsys_util.get_required_thirdparty_version(
            thirdparty_libs, 'Python')
        
        # TODO FIXME: ignored
        # python_version = python_version.replace('.', '')
        
        base_dir = os.path.join(
            self.thirdbase_dir,
            'Python',
            python_version)
        
        return (base_dir, python_version)
        
        
    def init(self, benv):

        base_dir, python_version = self._GetPythonDir(benv.required_thirdparty_libs)
        pythonlibname = 'python{ver}'.format(ver=python_version)

        env = benv.env

        env['PYTHONDIR'] = base_dir

        env['SCAFFOLD_PYTHON_VERSION'] = python_version

        env['CPPPATH'].extend([os.path.join(env['PYTHONDIR'], 'include')])
        env['LIBPATH'].extend([os.path.join(env['PYTHONDIR'], 'libs')])
        
        env['RPATH'].extend(env['LIBPATH'])
        env['LIBS'].extend([pythonlibname])


PLATFORM_MAP = [
    {
        'variants': {'platform_target': 'wasm_32'},
        'result': WasmPythonLib
    },
    {
        'variants': {'platform_target': 'ios'},
        'result': IOSPythonLib
    },
    {
        'variants': {'opsys': 'Linux'},
        'result': LinuxPythonLib
    },
    {
        'variants': {'opsys': 'Windows'},
        'result': WindowsPythonLib
    },
    {
        'variants': {'opsys': 'Darwin'},
        'result': DarwinPythonLib
    }
]