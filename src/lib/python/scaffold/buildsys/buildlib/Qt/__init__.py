

import os

import scaffold.variant

from .. import ThirdbaseLib, Builder

from ... import util as buildsys_util


class MocBuilder(Builder):

    def __init__(self, *args, **kwargs):
        Builder.__init__(self, *args, **kwargs)

        self.benv.cpps_pre_moc = self.benv.cpps[:]
        self.benv.cpps += self.outputs


    def _get_moc_output_path(self, cpp_entry, json=False):
        result = os.path.join(
            self.benv.sset_gen_lib_dir,
            'moc_{}'.format(os.path.basename(cpp_entry.replace('.h', '.cpp')))
        )

        if json:
            result += '.json'

        return result


    @property
    def outputs(self):
        os_list = []
        for cpp_entry in self.benv.cpps_pre_moc:
            os_list.append(self._get_moc_output_path(cpp_entry))

        return os_list

    def _gen_cmd(self):

        env = self.benv.env

        bin_dir = 'libexec'
        if os.name == 'nt':
            bin_dir = 'bin'
        if scaffold.variant.get_variant('arch') == 'aarch64':
              bin_dir = 'lib/qt6'
  
        moc_defines = ''
        if scaffold.variant.get_variant('platform_target') == 'wasm_32':
            moc_defines = '-DSCAFFOLD_WASM'

        moc_exec_path = os.path.join(env['DIR.QT'], bin_dir, 'moc')
        if os.name == 'nt':
            moc_exec_path += '.exe'

        moc_exec_path += ' --output-json {} -o $out $in'.format(moc_defines)

        return moc_exec_path


    def gen_rules(self):

        env = self.benv.env

        n  = '\n'
        n += 'rule moc\n'
        n += '    command = {}\n\n'.format(self._gen_cmd())

        return n


    def gen_build(self):

        n  = '\n'
        for header_entry in self.benv.headers:

            n += 'build {} | {}: moc {}\n'.format(
                self._get_moc_output_path(header_entry),
                self._get_moc_output_path(header_entry, json=True),
                header_entry
            )


        return n


class RCCBuilder(Builder):

    @property
    def outputs(self):
        
        if 'resource_dir' in self.benv.interface:
            cpp_out = os.path.join(
                self.benv.sset_gen_lib_dir,
                '{}_{}_resources.cpp'.format(self.benv.sset_name, self.benv.lib_name)
            )
            return [cpp_out]

        return []

    def _gen_cmd(self):
        env = self.benv.env

        bin_dir = 'libexec'
        if os.name == 'nt':
            bin_dir = 'bin'
            
        if scaffold.variant.get_variant('arch') == 'aarch64':
            bin_dir = 'lib/qt6'
  
        rcc_exec_path = os.path.join(env['DIR.QT'], bin_dir, 'rcc')
        if os.name == 'nt':
            rcc_exec_path += '.exe'

        sc_rcc_cmd = 'sc_rcc'
        if os.name == 'nt':
            sc_rcc_cmd = r'C:\Users\justi\dev\scaffold_root\scninja\src\bin\sc_rcc.bat'

        cmd = '{} --rcc {} --root_dir {} --output $out --input $in\n\n'.format(
            sc_rcc_cmd, rcc_exec_path, self.benv.root_dir
        )

        return cmd

    def gen_rules(self):

        env = self.benv.env

        n  = '\n'
        n += 'rule rcc\n'
        n += '    command = {}\n\n'.format(self._gen_cmd())

        return n

    def gen_build(self):

        n = '\n'
        if 'resource_dir' in self.benv.interface and self.benv.resource_dir:
            input_sscript = os.path.join(self.benv.product_dir, self.benv.resource_dir, 'ScaffoldScript')

            n += 'build {}: rcc {}\n'.format(self.outputs[0], input_sscript)
            n += '    sc_script = {}\n'.format(input_sscript)

            self.benv.cpps.append(self.outputs[0])


        return n


class QtLib(ThirdbaseLib):

    BUILDERS = {
        'Moc': MocBuilder,
        'RCC': RCCBuilder
    }

    def get_lib_dir(self, benv):
        return os.path.join(benv.env['DIR.QT'], 'lib')


    def _GetQtDir(self, thirdparty_libs):

        qt_version = buildsys_util.get_required_thirdparty_version(
            thirdparty_libs, 'Qt')
        
        qt_dir =  os.path.join(self.thirdbase_dir, 'Qt', qt_version)
        return (qt_version, qt_dir)


    def init(self, benv):

        env = benv.env
        qt_version, qt_dir = self._GetQtDir(benv.required_thirdparty_libs)

        env['DIR.QT'] = qt_dir

        env['CPPPATH'].extend([
            os.path.join(env['DIR.QT'], 'include')
        ])

        env['LIBPATH'].insert(0, os.path.join(env['DIR.QT'], 'lib'))

        # env['RPATH'].extend(env['LIBPATH'])

        # TODO: moc autoscan. Right now we're just running moc on everything
        # if the build target requires Qt
        # QtLib.initMoc(env)


class LinuxQtLib(QtLib):

    def _GetQtDir(self, thirdparty_libs):
        qt_version, qt_dir = QtLib._GetQtDir(self, thirdparty_libs)
        qt_dir = os.path.join(qt_dir, 'gcc_64')
        return (qt_version, qt_dir)
        
    def init(self, benv):
        QtLib.init(self, benv)

        qt_version, qt_dir = self._GetQtDir(benv.required_thirdparty_libs)
        env = benv.env

        qtlibs = ['Core',
                  'DBus',
                  'Gui',
                  'Svg',
                  'Sql',
                  'Xml',
                  'Widgets',
                  'Multimedia',
                   # 'X11Extras', # Note Linux/X11 Only
                  'OpenGL',
                  'OpenGLWidgets',
                  'Quick',
                  'Qml',
                  'Network',
                  'WebSockets',
                   # 'WebEngine',
                  'WebEngineCore',
                  'WebChannel',
                  'WebEngineWidgets',
                  'WebEngineQuick',
                  'WebChannelQuick'

                   #'Sensors', # required for Qt6WebKit
                   # 'Qml', # required for Qt6WebKit
                   # 'WebKit',
                   # 'WebKitWidgets']
        ]
        qt_version_major = qt_version.split('.')[0]
        qtlibs = ['Qt{}{}'.format(qt_version_major, lib_name) for lib_name in qtlibs]
        env['LIBS'].extend(qtlibs)

        qt_dir = env['DIR.QT']
        env['CPPPATH'].extend([
            os.path.join(qt_dir, 'include', 'QtCore'),
            os.path.join(qt_dir, 'include', 'QtGui'),
            os.path.join(qt_dir, 'include', 'QtWidgets'),
            os.path.join(qt_dir, 'include', 'QtOpenGLWidgets'),
            os.path.join(qt_dir, 'include', 'QtOpenGL')
        ])

        qnp_base_dir = os.path.join(self.thirdbase_dir, 'qnanopainter', qt_version, 'gcc_64')
        env['LIBS'].append('qnanopainter')
        env['LIBPATH'].append(os.path.join(qnp_base_dir, 'lib'))
        env['CPPPATH'].append(os.path.join(qnp_base_dir, 'include'))

        '''
        '3DCore',
        '3DInput',
        '3DRender',
        '3DInput',
        '3DExtras',
        '3DQuick',
        '3DQuickInput',
        '3DQuickRender',
        '3DQuickExtras'
        '''
class DarwinQtLib(QtLib):

    def _GetQtDir(self, thirdparty_libs):
        qt_version, qt_dir = QtLib._GetQtDir(self, thirdparty_libs)
        qt_dir = os.path.join(qt_dir, 'macos')
        return (qt_version, qt_dir)

    def init(self, benv):
        QtLib.init(self, benv)

        env = benv.env
        qt_version, qt_dir = self._GetQtDir(benv.required_thirdparty_libs)
        env['QTDIR'] = qt_dir
        
        qtlibs = ['Core',
                  'DBus',
                  'Gui',
                  'Svg',
                  'Sql',
                  'Xml',
                  'Widgets',
                  'Multimedia',
                  'OpenGL',
                  'OpenGLWidgets',
                  'Quick',
                  'Network',
                  'WebSockets',
                  'WebEngineCore',
                  'WebChannel',
                  'WebEngineWidgets',
                  'WebEngineQuick',
                  'WebChannelQuick'
                   # 'Sensors', # required for Qt6WebKit
                   # 'Qml', # required for Qt6WebKit
                   # 'WebKit',
                   # 'WebKitWidgets']
        ]
        qtlibs = ['Qt{}'.format(lib_name) for lib_name in qtlibs]
        env['FRAMEWORKS'].extend(qtlibs)
        env['FRAMEWORKS'].append('OpenGL')

        env['FRAMEWORKPATH'].append(os.path.join(env['DIR.QT'], 'lib'))

        env['CPPPATH'].extend([
            os.path.join(qt_dir, 'lib', 'QtCore.framework', 'Headers'),
            os.path.join(qt_dir, 'lib', 'QtGui.framework', 'Headers'),
            os.path.join(qt_dir, 'lib', 'QtWidgets.framework', 'Headers'),
            os.path.join(qt_dir, 'lib', 'QtOpenGL.framework', 'Headers'),
            # os.path.join(qt_dir, 'lib', 'QtOpenGLWidgets.framework', 'Headers'),
        ])

        qnp_base_dir = os.path.join(self.thirdbase_dir, 'qnanopainter', qt_version, 'macos')
        env['LIBS'].append('qnanopainter')
        env['LIBPATH'].append(os.path.join(qnp_base_dir, 'lib'))
        env['CPPPATH'].append(os.path.join(qnp_base_dir, 'include'))


class IOSQtLib(QtLib):

    def _GetQtDir(self, thirdparty_libs):
        qt_version, qt_dir = QtLib._GetQtDir(self, thirdparty_libs)
        qt_dir = os.path.join(qt_dir, 'ios')
        return (qt_version, qt_dir)

    def init(self, benv):
        QtLib.init(self, benv)

        env = benv.env
        qt_version, qt_dir = self._GetQtDir(benv.required_thirdparty_libs)
        env['QTDIR'] = qt_dir
        
        qtlibs = ['Core',
                  'Gui',
                  'Svg',
                  'Sql',
                  'Xml',
                  'Widgets',
                  'Multimedia',
                  'OpenGL',
                  'Quick',
                  'Network',
                  'WebSockets'
        ]

        env['CPPPATH'].append(os.path.join(qt_dir, 'mkspecs', 'macx-ios-clang'))

        for qt_entry in qtlibs:
            env['CPPPATH'].append(os.path.join(qt_dir, 'include', 'Qt{}'.format(qt_entry)))
            env['CPPDEFINES'].append('QT_{}_LIB'.format(qt_entry.upper()))

        qnp_base_dir = os.path.join(self.thirdbase_dir, 'qnanopainter', qt_version, 'ios')
        env['LIBS'].append('qnanopainter')
        env['LIBPATH'].append(os.path.join(qnp_base_dir, 'lib'))
        env['CPPPATH'].append(os.path.join(qnp_base_dir, 'include'))


class WasmQtLib(QtLib):

    def init(self, benv):
        QtLib.init(self, benv)

        env = benv.env

        for key in ['CPPDEFINES', 'CPPPATH', 'LINKFLAGS']:
            if key not in env:
                print('defining env list key "{}"'.format(key))
                env[key] = []


        env['CPPDEFINES'].append('SCAFFOLD_WASM')

        # 'QT_QML_DEBUG'
        # NOTE: QtSql not available in wasm_32 for Qt 5.14.1
        #
        env['CPPDEFINES'].extend([
            'QT_DEPRECATED_WARNINGS',
            'QT_WIDGETS_LIB',
            'QT_GUI_LIB',
            'QT_CORE_LIB',
            'QT_SVG_LIB',
            # 'QT_SQL_LIB',
            'QT_NETWORK_LIB',
            'QT_MULTIMEDIA_LIB',
            'QT_WEBSOCKETS_LIB'
        ])

        env['CPPPATH'].extend([
            '/home/justinottley/.emscripten_ports/openssl/include',
            os.path.join(env['DIR.QT'], 'mkspecs', 'wasm-emscripten')
        ])
        
        # -s WASM=1 -s FULL_ES2=1 -s FULL_ES3=1 -s USE_WEBGL2=1 -s NO_EXIT_RUNTIME=0 -s ERROR_ON_UNDEFINED_SYMBOLS=1 -s EXTRA_EXPORTED_RUNTIME_METHODS=["UTF16ToString","stringToUTF16"] --bind -s FETCH=1 -O2 -s USE_PTHREADS=1 -s PTHREAD_POOL_SIZE=4 -s TOTAL_MEMORY=1GB

        
        libs_all = [
            'plugins/imageformats/objects-Release/QGifPlugin_init/QGifPlugin_init.cpp.o',
            'plugins/imageformats/objects-Release/QICNSPlugin_init/QICNSPlugin_init.cpp.o',
            'plugins/imageformats/objects-Release/QICOPlugin_init/QICOPlugin_init.cpp.o',
            'plugins/imageformats/objects-Release/QJpegPlugin_init/QJpegPlugin_init.cpp.o',
            'plugins/iconengines/objects-Release/QSvgIconPlugin_init/QSvgIconPlugin_init.cpp.o',
            'plugins/imageformats/objects-Release/QSvgPlugin_init/QSvgPlugin_init.cpp.o',
            'plugins/imageformats/objects-Release/QTgaPlugin_init/QTgaPlugin_init.cpp.o',
            'plugins/imageformats/objects-Release/QTiffPlugin_init/QTiffPlugin_init.cpp.o',
            'plugins/platforms/objects-Release/QWasmIntegrationPlugin_init/QWasmIntegrationPlugin_init.cpp.o',
            'plugins/imageformats/objects-Release/QWbmpPlugin_init/QWbmpPlugin_init.cpp.o',
            'plugins/imageformats/objects-Release/QWebpPlugin_init/QWebpPlugin_init.cpp.o',
            'qml/QtQml/objects-Release/Qml_resources_1/.rcc/qrc_qmake_QtQml.cpp.o',
            'qml/QtQml/objects-Release/qmlplugin_init/qmlplugin_init.cpp.o',
            'qml/QtQml/Models/objects-Release/modelsplugin_init/modelsplugin_init.cpp.o',
            'qml/QtQml/Models/objects-Release/QmlModels_resources_1/.rcc/qrc_qmake_QtQml_Models.cpp.o',
            'qml/QtQuick/objects-Release/qtquick2plugin_init/qtquick2plugin_init.cpp.o',
            'qml/QtQuick/objects-Release/Quick_resources_1/.rcc/qrc_qmake_QtQuick.cpp.o',
            'qml/QtQuick/objects-Release/qtquick2plugin_init/qtquick2plugin_init.cpp.o',
            'lib/libQt6BundledFreetype.a',
            'lib/libQt6BundledLibpng.a',
            'lib/libQt6BundledLibjpeg.a',
            'lib/objects-Release/QWasmIntegrationPlugin_resources_1/.rcc/qrc_wasmfonts.cpp.o',
            'lib/objects-Release/Gui_resources_1/.rcc/qrc_qpdf.cpp.o',
            'lib/objects-Release/Gui_resources_2/.rcc/qrc_gui_shaders.cpp.o',
            'lib/objects-Release/Widgets_resources_1/.rcc/qrc_qstyle.cpp.o',
            'lib/objects-Release/Widgets_resources_2/.rcc/qrc_qstyle1.cpp.o',
            'lib/objects-Release/Widgets_resources_3/.rcc/qrc_qmessagebox.cpp.o',
            'lib/objects-Release/Quick_resources_2/.rcc/qrc_scenegraph_shaders.cpp.o',
            'plugins/platforms/libqwasm.a',
            'plugins/iconengines/libqsvgicon.a',
            'plugins/imageformats/libqgif.a',
            'plugins/imageformats/libqicns.a',
            'plugins/imageformats/libqico.a',
            'plugins/imageformats/libqjpeg.a',
            'plugins/imageformats/libqsvg.a',
            'plugins/imageformats/libqtga.a',
            'plugins/imageformats/libqtiff.a',
            'plugins/imageformats/libqwbmp.a',
            'plugins/imageformats/libqwebp.a',
            'plugins/tls/libqcertonlybackend.a',
            'qml/QtQml/Models/libmodelsplugin.a',
            'qml/QtQml/libqmlplugin.a',
            'qml/QtQuick/libqtquick2plugin.a',
            'lib/libQt6Quick.a',
            'lib/libQt6QmlModels.a',
            'lib/libQt6Qml.a',
            'lib/libQt6Multimedia.a',
            'lib/libQt6Widgets.a',
            'lib/libQt6Svg.a',
            'lib/libQt6Xml.a',
            'lib/libQt6OpenGL.a',
            'lib/libQt6OpenGLWidgets.a',
            'lib/libQt6Gui.a',
            'lib/libQt6BundledHarfbuzz.a',
            'lib/libQt6BundledFreetype.a',
            'lib/libQt6BundledLibpng.a',
            'lib/libQt6WebSockets.a',
            'lib/libQt6Network.a',
            'lib/libQt6Core.a',
            'lib/libQt6BundledZLIB.a',
            'lib/libQt6BundledPcre2.a'
        ]


        for lib_entry in libs_all:
            env['LINKFLAGS'].append(os.path.join(env['DIR.QT'], lib_entry))


        # QtLib.initMoc(env)


class WasmSTQtLib(WasmQtLib):

    def _GetQtDir(self, thirdparty_libs):
        qt_dir_base = QtLib._GetQtDir(self, thirdparty_libs)
        return os.path.join(qt_dir_base, 'wasm_32')


    def init(self, benv):
        WasmQtLib.init(self, benv)

        env = benv.env

        if 'LINKFLAGS' not in env:
            env['LINKFLAGS'] = []

        env['LINKFLAGS'] = [
            '-sWASM=1',
            '-sFULL_ES2=1',
            '-sFULL_ES3=1',
            '-sUSE_WEBGL2=1',
            '-sERROR_ON_UNDEFINED_SYMBOLS=1',
            '-sEXPORTED_RUNTIME_METHODS=[UTF16ToString,stringToUTF16]',
            '-sFETCH=1',
            '-sMODULARIZE=1',
            '-sEXPORT_NAME=createQtAppInstance',
            '-sASSERTIONS=2',
            '-sDEMANGLE_SUPPORT=1',
            '-sGL_DEBUG=1',
            '-sALLOW_MEMORY_GROWTH=1',
            '-sINITIAL_MEMORY=50MB',
            '-g2',
            '--bind',
            '--profiling-funcs',
            '-sASYNCIFY_IMPORTS=qt_asyncify_suspend_js,qt_asyncify_resume_js',
            '-sNO_DISABLE_EXCEPTION_CATCHING'
        ] + env['LINKFLAGS']

        # websocket.js required for emscripten_websocket api, required by audio
        env['LIBS'].append('websocket.js')

        # print(env['LINKFLAGS'])


class WasmST68QtLib(WasmQtLib):

    def _GetQtDir(self, thirdparty_libs):
        return '/home/justinottley/dev/revlens_root/thirdbase/22_09/Linux-x86_64/Qt/6.8.0/wasm_singlethread'


    def init(self, benv):
        QtLib.init(self, benv)
        env = benv.env

        for key in ['CPPDEFINES', 'CPPPATH', 'LINKFLAGS']:
            if key not in env:
                print('defining env list key "{}"'.format(key))
                env[key] = []


        env['CPPDEFINES'].append('SCAFFOLD_WASM')

        # 'QT_QML_DEBUG'
        # NOTE: QtSql not available in wasm_32 for Qt 5.14.1
        #
        env['CPPDEFINES'].extend([
            'QT_DEPRECATED_WARNINGS',
            'QT_WIDGETS_LIB',
            'QT_GUI_LIB',
            'QT_CORE_LIB',
            'QT_SVG_LIB',
            # 'QT_SQL_LIB',
            'QT_NETWORK_LIB',
            'QT_MULTIMEDIA_LIB',
            'QT_WEBSOCKETS_LIB'
        ])

        env['CPPPATH'].extend([
            '/home/justinottley/.emscripten_ports/openssl/include',
            os.path.join(env['DIR.QT'], 'mkspecs', 'wasm-emscripten')
        ])

        if 'LINKFLAGS' not in env:
            env['LINKFLAGS'] = []


        env['LINKFLAGS'] = [
            '-s INITIAL_MEMORY=50MB',
            '-s MAXIMUM_MEMORY=4GB',
            '-s EXPORTED_RUNTIME_METHODS=UTF16ToString,stringToUTF16,JSEvents,specialHTMLTargets,FS,callMain',
            '-s EXPORT_NAME=revlens_entry',
            '-s MAX_WEBGL_VERSION=2',
            '-s FETCH=1',
            '-s WASM_BIGINT=1',
            '-s STACK_SIZE=5MB',
            '-s MODULARIZE=1',
            # '-s DISABLE_EXCEPTION_CATCHING=1',
            '-sNO_DISABLE_EXCEPTION_CATCHING',
            '-s ALLOW_MEMORY_GROWTH',
            '-s DEMANGLE_SUPPORT=1',
            '--profiling-funcs',
            '-sASYNCIFY_IMPORTS=qt_asyncify_suspend_js,qt_asyncify_resume_js',
            '-s ERROR_ON_UNDEFINED_SYMBOLS=1'
        ] + env['LINKFLAGS']

        pre_out_link_list = \
        '''
        plugins/imageformats/objects-Release/QGifPlugin_init/QGifPlugin_init.cpp.o
        plugins/imageformats/objects-Release/QICNSPlugin_init/QICNSPlugin_init.cpp.o
        plugins/imageformats/objects-Release/QICOPlugin_init/QICOPlugin_init.cpp.o
        plugins/imageformats/objects-Release/QJpegPlugin_init/QJpegPlugin_init.cpp.o
        plugins/iconengines/objects-Release/QSvgIconPlugin_init/QSvgIconPlugin_init.cpp.o
        plugins/imageformats/objects-Release/QSvgPlugin_init/QSvgPlugin_init.cpp.o
        plugins/imageformats/objects-Release/QTgaPlugin_init/QTgaPlugin_init.cpp.o
        plugins/imageformats/objects-Release/QTiffPlugin_init/QTiffPlugin_init.cpp.o
        plugins/platforms/objects-Release/QWasmIntegrationPlugin_init/QWasmIntegrationPlugin_init.cpp.o
        plugins/imageformats/objects-Release/QWbmpPlugin_init/QWbmpPlugin_init.cpp.o
        plugins/imageformats/objects-Release/QWebpPlugin_init/QWebpPlugin_init.cpp.o
        plugins/tls/objects-Release/QTlsBackendCertOnlyPlugin_init/QTlsBackendCertOnlyPlugin_init.cpp.o
        '''

        env['CXX_PRE_OUT_FLAGS'] = ''
        for entry in pre_out_link_list.split():
            env['CXX_PRE_OUT_FLAGS'] += os.path.join(env['DIR.QT'], entry.strip())
            env['CXX_PRE_OUT_FLAGS'] += ' '


        post_out_link_list = \
        '''
        lib/objects-Release/Gui_resources_1/.rcc/qrc_qpdf_init.cpp.o
        lib/objects-Release/Gui_resources_2/.rcc/qrc_gui_shaders_init.cpp.o
        ./qml/QtQuick/objects-Release/Quick_resources_1/.rcc/qrc_qmake_QtQuick_init.cpp.o
        lib/objects-Release/Quick_resources_2/.rcc/qrc_scenegraph_shaders_init.cpp.o
        lib/objects-Release/Quick_resources_3/.rcc/qrc_scenegraph_curve_shaders_init.cpp.o
        lib/objects-Release/Quick_resources_4/.rcc/qrc_scenegraph_curve_shaders_derivatives_init.cpp.o
        lib/objects-Release/Quick_resources_5/.rcc/qrc_scenegraph_curve_shaders_lg_init.cpp.o
        lib/objects-Release/Quick_resources_6/.rcc/qrc_scenegraph_curve_shaders_lg_derivatives_init.cpp.o
        lib/objects-Release/Quick_resources_7/.rcc/qrc_scenegraph_curve_shaders_rg_init.cpp.o
        lib/objects-Release/Quick_resources_8/.rcc/qrc_scenegraph_curve_shaders_rg_derivatives_init.cpp.o
        lib/objects-Release/Quick_resources_9/.rcc/qrc_scenegraph_curve_shaders_cg_init.cpp.o
        lib/objects-Release/Quick_resources_10/.rcc/qrc_scenegraph_curve_shaders_cg_derivatives_init.cpp.o
        lib/objects-Release/Widgets_resources_1/.rcc/qrc_qstyle_init.cpp.o
        lib/objects-Release/Widgets_resources_2/.rcc/qrc_qstyle1_init.cpp.o
        lib/objects-Release/Widgets_resources_3/.rcc/qrc_qstyle_fusion_init.cpp.o
        lib/objects-Release/Widgets_resources_4/.rcc/qrc_qmessagebox_init.cpp.o
        ./qml/QtQml/Base/objects-Release/Qml_resources_1/.rcc/qrc_qmake_QtQml_Base_init.cpp.o
        lib/objects-Release/Qml_resources_2/.rcc/qrc_qmlMetaQmldir_init.cpp.o
        ./qml/QtQuick/objects-Release/qtquick2plugin_init/qtquick2plugin_init.cpp.o
        ./qml/QtQml/objects-Release/QmlMeta_resources_1/.rcc/qrc_qmake_QtQml_init.cpp.o
        ./qml/QtQml/objects-Release/QmlMeta_init/QmlMeta_init.cpp.o
        ./qml/QtQml/Base/objects-Release/qmlplugin_init/qmlplugin_init.cpp.o
        ./qml/QtQml/Models/objects-Release/modelsplugin_init/modelsplugin_init.cpp.o
        ./qml/QtQuick/Controls/objects-Release/qtquickcontrols2plugin_init/qtquickcontrols2plugin_init.cpp.o
        lib/objects-Release/qtquickcontrols2plugin_resources_1/.rcc/qrc_indirectBasic_init.cpp.o
        ./qml/QtQuick/Controls/Fusion/objects-Release/qtquickcontrols2fusionstyleplugin_resources_1/.rcc/qrc_qmake_QtQuick_Controls_Fusion_init.cpp.o
        ./qml/QtQuick/Controls/Fusion/objects-Release/qtquickcontrols2fusionstyleplugin_resources_2/.rcc/qrc_qtquickcontrols2fusionstyleplugin_raw_qml_0_init.cpp.o
        ./qml/QtQuick/Controls/Fusion/objects-Release/qtquickcontrols2fusionstyleplugin_init/qtquickcontrols2fusionstyleplugin_init.cpp.o
        lib/objects-Release/qtquickcontrols2fusionstyleplugin_resources_3/.rcc/qrc_qtquickcontrols2fusionstyle_init.cpp.o
        ./qml/QtQuick/Controls/Material/objects-Release/qtquickcontrols2materialstyleplugin_resources_1/.rcc/qrc_qmake_QtQuick_Controls_Material_init.cpp.o
        ./qml/QtQuick/Controls/Material/objects-Release/qtquickcontrols2materialstyleplugin_resources_2/.rcc/qrc_qtquickcontrols2materialstyleplugin_raw_qml_0_init.cpp.o
        ./qml/QtQuick/Controls/Material/objects-Release/qtquickcontrols2materialstyleplugin_init/qtquickcontrols2materialstyleplugin_init.cpp.o
        lib/objects-Release/qtquickcontrols2materialstyleplugin_resources_3/.rcc/qrc_qtquickcontrols2materialstyleplugin_init.cpp.o
        lib/objects-Release/qtquickcontrols2materialstyleplugin_resources_4/.rcc/qrc_qtquickcontrols2materialstyleplugin_shaders_init.cpp.o
        ./qml/QtQuick/Controls/Imagine/objects-Release/qtquickcontrols2imaginestyleplugin_resources_1/.rcc/qrc_qmake_QtQuick_Controls_Imagine_init.cpp.o
        ./qml/QtQuick/Controls/Imagine/objects-Release/qtquickcontrols2imaginestyleplugin_resources_2/.rcc/qrc_qtquickcontrols2imaginestyleplugin_raw_qml_0_init.cpp.o
        ./qml/QtQuick/Controls/Imagine/objects-Release/qtquickcontrols2imaginestyleplugin_init/qtquickcontrols2imaginestyleplugin_init.cpp.o
        lib/objects-Release/qtquickcontrols2imaginestyleplugin_resources_3/.rcc/qrc_qmake_qtquickcontrols2imaginestyleplugin_init.cpp.o
        ./qml/QtQuick/Controls/Universal/objects-Release/qtquickcontrols2universalstyleplugin_resources_1/.rcc/qrc_qmake_QtQuick_Controls_Universal_init.cpp.o
        ./qml/QtQuick/Controls/Universal/objects-Release/qtquickcontrols2universalstyleplugin_resources_2/.rcc/qrc_qtquickcontrols2universalstyleplugin_raw_qml_0_init.cpp.o
        ./qml/QtQuick/Controls/Universal/objects-Release/qtquickcontrols2universalstyleplugin_init/qtquickcontrols2universalstyleplugin_init.cpp.o
        lib/objects-Release/qtquickcontrols2universalstyleplugin_resources_3/.rcc/qrc_qtquickcontrols2universalstyleplugin_init.cpp.o
        ./qml/QtQuick/Controls/Basic/objects-Release/qtquickcontrols2basicstyleplugin_resources_1/.rcc/qrc_qmake_QtQuick_Controls_Basic_init.cpp.o
        ./qml/QtQuick/Controls/Basic/objects-Release/qtquickcontrols2basicstyleplugin_resources_2/.rcc/qrc_qtquickcontrols2basicstyleplugin_raw_qml_0_init.cpp.o
        ./qml/QtQuick/Controls/Basic/objects-Release/qtquickcontrols2basicstyleplugin_init/qtquickcontrols2basicstyleplugin_init.cpp.o
        lib/objects-Release/qtquickcontrols2basicstyleplugin_resources_3/.rcc/qrc_qtquickcontrols2basicstyleplugin_init.cpp.o
        ./qml/QtQuick/Templates/objects-Release/qtquicktemplates2plugin_init/qtquicktemplates2plugin_init.cpp.o
        ./qml/QtQuick/Controls/impl/objects-Release/qtquickcontrols2implplugin_init/qtquickcontrols2implplugin_init.cpp.o
        ./qml/QtQuick/Controls/Fusion/impl/objects-Release/qtquickcontrols2fusionstyleimplplugin_resources_1/.rcc/qrc_qmake_QtQuick_Controls_Fusion_impl_init.cpp.o
        ./qml/QtQuick/Controls/Fusion/impl/objects-Release/qtquickcontrols2fusionstyleimplplugin_resources_2/.rcc/qrc_qtquickcontrols2fusionstyleimplplugin_raw_qml_0_init.cpp.o
        ./qml/QtQuick/Controls/Fusion/impl/objects-Release/qtquickcontrols2fusionstyleimplplugin_init/qtquickcontrols2fusionstyleimplplugin_init.cpp.o
        ./qml/QtQuick/Window/objects-Release/quickwindow_resources_1/.rcc/qrc_qmake_QtQuick_Window_init.cpp.o
        ./qml/QtQuick/Window/objects-Release/quickwindow_init/quickwindow_init.cpp.o
        ./qml/QtQuick/Controls/Material/impl/objects-Release/qtquickcontrols2materialstyleimplplugin_resources_1/.rcc/qrc_qmake_QtQuick_Controls_Material_impl_init.cpp.o
        ./qml/QtQuick/Controls/Material/impl/objects-Release/qtquickcontrols2materialstyleimplplugin_resources_2/.rcc/qrc_qtquickcontrols2materialstyleimplplugin_raw_qml_0_init.cpp.o
        ./qml/QtQuick/Controls/Material/impl/objects-Release/qtquickcontrols2materialstyleimplplugin_init/qtquickcontrols2materialstyleimplplugin_init.cpp.o
        ./qml/QtQuick/Controls/Imagine/impl/objects-Release/qtquickcontrols2imaginestyleimplplugin_resources_1/.rcc/qrc_qmake_QtQuick_Controls_Imagine_impl_init.cpp.o
        ./qml/QtQuick/Controls/Imagine/impl/objects-Release/qtquickcontrols2imaginestyleimplplugin_resources_2/.rcc/qrc_qtquickcontrols2imaginestyleimplplugin_raw_qml_0_init.cpp.o
        ./qml/QtQuick/Controls/Imagine/impl/objects-Release/qtquickcontrols2imaginestyleimplplugin_init/qtquickcontrols2imaginestyleimplplugin_init.cpp.o
        lib/objects-Release/qtquickcontrols2imaginestyleimplplugin_resources_3/.rcc/qrc_qtquickcontrols2imaginestyleimplplugin_shaders_init.cpp.o
        ./qml/QtQuick/Controls/Universal/impl/objects-Release/qtquickcontrols2universalstyleimplplugin_resources_1/.rcc/qrc_qmake_QtQuick_Controls_Universal_impl_init.cpp.o
        ./qml/QtQuick/Controls/Universal/impl/objects-Release/qtquickcontrols2universalstyleimplplugin_resources_2/.rcc/qrc_qtquickcontrols2universalstyleimplplugin_raw_qml_0_init.cpp.o
        ./qml/QtQuick/Controls/Universal/impl/objects-Release/qtquickcontrols2universalstyleimplplugin_init/qtquickcontrols2universalstyleimplplugin_init.cpp.o
        ./qml/QtQuick/Controls/Basic/impl/objects-Release/qtquickcontrols2basicstyleimplplugin_resources_1/.rcc/qrc_qmake_QtQuick_Controls_Basic_impl_init.cpp.o
        ./qml/QtQuick/Controls/Basic/impl/objects-Release/qtquickcontrols2basicstyleimplplugin_init/qtquickcontrols2basicstyleimplplugin_init.cpp.o
        ./qml/QtQuick/Shapes/objects-Release/qmlshapesplugin_init/qmlshapesplugin_init.cpp.o
        lib/objects-Release/QWasmIntegrationPlugin_resources_1/.rcc/qrc_wasmfonts_init.cpp.o
        lib/objects-Release/QWasmIntegrationPlugin_resources_2/.rcc/qrc_wasmwindow_init.cpp.o
        ./qml/QtQml/Models/objects-Release/QmlModels_resources_1/.rcc/qrc_qmake_QtQml_Models_init.cpp.o
        ./qml/QtQuick/Controls/objects-Release/QuickControls2_resources_1/.rcc/qrc_qmake_QtQuick_Controls_init.cpp.o
        ./qml/QtQuick/Templates/objects-Release/QuickTemplates2_resources_1/.rcc/qrc_qmake_QtQuick_Templates_init.cpp.o
        ./qml/QtQuick/Controls/impl/objects-Release/QuickControls2Impl_resources_1/.rcc/qrc_qmake_QtQuick_Controls_impl_init.cpp.o
        ./qml/QtQuick/Shapes/objects-Release/QuickShapesPrivate_resources_1/.rcc/qrc_qmake_QtQuick_Shapes_init.cpp.o
        lib/objects-Release/QuickShapesPrivate_resources_2/.rcc/qrc_qtquickshapes_shaders_init.cpp.o
        lib/libQt6Core.a
        lib/libQt6Gui.a
        lib/libQt6Quick.a
        lib/libQt6Widgets.a
        lib/libQt6Qml.a
        ./qml/QtQuick/libqtquick2plugin.a
        ./qml/QtQml/libqmlmetaplugin.a
        ./qml/QtQml/Base/libqmlplugin.a
        ./qml/QtQml/Models/libmodelsplugin.a
        ./qml/QtQuick/Controls/libqtquickcontrols2plugin.a
        ./qml/QtQuick/Controls/Fusion/libqtquickcontrols2fusionstyleplugin.a
        ./qml/QtQuick/Controls/Material/libqtquickcontrols2materialstyleplugin.a
        ./qml/QtQuick/Controls/Imagine/libqtquickcontrols2imaginestyleplugin.a
        ./qml/QtQuick/Controls/Universal/libqtquickcontrols2universalstyleplugin.a
        ./qml/QtQuick/Controls/Basic/libqtquickcontrols2basicstyleplugin.a
        ./qml/QtQuick/Templates/libqtquicktemplates2plugin.a
        ./qml/QtQuick/Controls/impl/libqtquickcontrols2implplugin.a
        ./qml/QtQuick/Controls/Fusion/impl/libqtquickcontrols2fusionstyleimplplugin.a
        ./qml/QtQuick/Window/libquickwindowplugin.a
        ./qml/QtQuick/Controls/Material/impl/libqtquickcontrols2materialstyleimplplugin.a
        ./qml/QtQuick/Controls/Imagine/impl/libqtquickcontrols2imaginestyleimplplugin.a
        ./qml/QtQuick/Controls/Universal/impl/libqtquickcontrols2universalstyleimplplugin.a
        ./qml/QtQuick/Controls/Basic/impl/libqtquickcontrols2basicstyleimplplugin.a
        ./qml/QtQuick/Shapes/libqmlshapesplugin.a
        ./plugins/imageformats/libqgif.a
        ./plugins/imageformats/libqicns.a
        ./plugins/imageformats/libqico.a
        ./plugins/imageformats/libqjpeg.a
        ./plugins/iconengines/libqsvgicon.a
        ./plugins/imageformats/libqsvg.a
        ./plugins/imageformats/libqtga.a
        ./plugins/imageformats/libqtiff.a
        ./plugins/platforms/libqwasm.a
        ./plugins/imageformats/libqwbmp.a
        ./plugins/imageformats/libqwebp.a
        ./plugins/tls/libqcertonlybackend.a
        ./qml/QtQuick/Controls/libqtquickcontrols2plugin.a
        ./qml/QtQuick/Controls/impl/libqtquickcontrols2implplugin.a
        ./qml/QtQuick/Templates/libqtquicktemplates2plugin.a
        lib/libQt6QuickControls2Impl.a
        lib/libQt6QuickControls2.a
        lib/libQt6QuickTemplates2.a
        ./qml/QtQuick/libqtquick2plugin.a
        ./qml/QtQml/Models/libmodelsplugin.a
        ./qml/QtQml/libqmlmetaplugin.a
        ./qml/QtQml/Base/libqmlplugin.a
        ./qml/QtQml/libqmlmetaplugin.a
        ./qml/QtQml/Base/libqmlplugin.a
        lib/libQt6QuickShapes.a
        lib/libQt6Quick.a
        lib/libQt6QmlModels.a
        lib/libQt6Qml.a
        lib/libQt6Multimedia.a
        lib/libQt6QmlBuiltins.a
        lib/libQt6BundledLibjpeg.a
        lib/libQt6Svg.a
        lib/libQt6Xml.a
        lib/libQt6OpenGL.a
        lib/libQt6Gui.a
        lib/libQt6BundledHarfbuzz.a
        lib/libQt6BundledFreetype.a
        lib/libQt6BundledLibpng.a
        lib/libQt6WebSockets.a
        lib/libQt6Network.a
        lib/libQt6Core.a
        lib/libQt6BundledZLIB.a
        lib/libQt6BundledPcre2.a
        '''

        env['CXX_LINK_FLAGS'] = ''
        for entry in post_out_link_list.split():
            env['CXX_LINK_FLAGS'] += os.path.join(env['DIR.QT'], entry.strip())
            env['CXX_LINK_FLAGS'] += ' '
            pass

        env['CXX_LINK_FLAGS'] += ' -lembind'

        isystem_list = \
        '''
        include/QtQml/6.8.0
        include/QtQml/6.8.0/QtQml
        include/QtCore/6.8.0
        include/QtCore/6.8.0/QtCore
        include/QtCore
        include
        mkspecs/wasm-emscripten
        include/QtQmlBuiltins/6.8.0
        include/QtQmlBuiltins/6.8.0/QtQmlBuiltins
        include/QtQmlBuiltins
        include/QtQml
        include/QtQmlIntegration
        include/QtNetwork
        include/QtGui
        include/QtQuick
        include/QtQmlModels
        include/QtOpenGL
        include/QtWidgets 
        '''

        env['ISYSTEMPATH'] = [os.path.join(env['DIR.QT'], ist.strip()) for ist in isystem_list.split()]

        # websocket.js required for emscripten_websocket api, required by audio
        env['LIBS'].append('websocket.js')


class WasmMTQtLib(WasmQtLib):

    def _GetQtDir(self, thirdparty_libs):
        return '/home/justinottley/dev/revlens_root/thirdbase/22_09/Linux-x86_64/Qt/6.7.0/wasm_multithread'

    def init(self, benv):
        WasmQtLib.init(self, benv)

        env = benv.env

        if 'LINKFLAGS' not in env:
            env['LINKFLAGS'] = []

        env['LINKFLAGS'] = [
            '--profiling-funcs',
            '-pthread',
            '-s PTHREAD_POOL_SIZE=4',
            '-s INITIAL_MEMORY=50MB',
            '-s EXPORTED_RUNTIME_METHODS=UTF16ToString,stringToUTF16,JSEvents,specialHTMLTargets,FS',
            '-s EXPORT_NAME=revlens',
            '-s MAX_WEBGL_VERSION=2',
            '-s FETCH=1',
            '-s WASM_BIGINT=1',
            '-s STACK_SIZE=5MB',
            '-s MODULARIZE=1',
            '-s DISABLE_EXCEPTION_CATCHING=1',
            '-s ALLOW_MEMORY_GROWTH',
            '-s DEMANGLE_SUPPORT=1',
            '-s ASYNCIFY_IMPORTS=qt_asyncify_suspend_js,qt_asyncify_resume_js',
            '-s ERROR_ON_UNDEFINED_SYMBOLS=1'
        ] + env['LINKFLAGS']

        # websocket.js required for emscripten_websocket api, required by audio
        env['LIBS'].append('websocket.js')

class WindowsQtLib(QtLib):

    def _GetQtDir(self, thirdparty_libs):
        
        qt_version = scaffold.buildsys.util.get_required_thirdparty_version(
            thirdparty_libs, 'Qt')
        
        qt_version = '6.4.2'
        return os.path.join(self.thirdbase_dir, 'Qt', qt_version, 'msvc2019_64')


    def init(self, benv):
        QtLib.init(self, benv)

        env = benv.env
        env['LIBS'].extend(['Qt6Cored',
                            'Qt6Guid',
                            'Qt6Svgd',
                            'Qt6Sqld',
                            'Qt6Xmld',
                            'Qt6Widgetsd',
                            'Qt6Multimediad',
                            'Qt6OpenGLd',
                            'Qt6Quickd',
                            'Qt6Networkd',
                            'Qt6WebSocketsd',
                            'Qt6WebEngineCored',
                            'Qt6WebChanneld',
                            'Qt6WebEngineWidgetsd'])
        
        env['LIBS'].extend(['OpenGL32'])
        
        env['CPPDEFINES'].extend([
            'QT_DEPRECATED_WARNINGS',
            'QT_CORE_LIB',
            'QT_GUI_LIB',
            'QT_SVG_LIB',
            'QT_SQL_LIB',
            'QT_WIDGETS_LIB',
            'QT_MULTIMEDIA_LIB',
            'QT_OPENGL_LIB',
            'QT_NETWORK_LIB',
            'QT_WEBSOCKETS_LIB'
        ])

class AndroidTermuxQtLib(QtLib):
    def _GetQtDir(self, thirdparty_libs):
        return ('6.8', os.getenv('PREFIX'))
        
    def init(self, benv):
        QtLib.init(self, benv)
        
        env = benv.env
  
        env['LIBS'].extend([
            'GL',
            'Qt6Core',
            'Qt6DBus',
            'Qt6Gui',
            'Qt6OpenGL',
            'Qt6Widgets',
            'Qt6Network',
            'Qt6Svg',
            'Qt6Sql',
            'Qt6Xml',
            'Qt6WebSockets',
            'Qt6Quick'
        ])
        
        env['CPPPATH'].extend([
            os.path.join(env['DIR.QT'], 'include', 'qt6')])
            
        env['LIBPATH'].insert(0, os.path.join(env['DIR.QT'], 'lib', 'qt6'))
        
        qt_dir = env['DIR.QT']
        env['CPPPATH'].extend([
            os.path.join(qt_dir, 'include', 'qt6', 'QtCore'),
            os.path.join(qt_dir, 'include', 'qt6', 'QtGui'),
            os.path.join(qt_dir, 'include', 'qt6', 'QtWidgets'),
            os.path.join(qt_dir, 'include', 'qt6', 'QtOpenGLWidgets'),
            os.path.join(qt_dir, 'include', 'qt6', 'QtOpenGL')
        ])

        qnp_base_dir = os.path.join(self.thirdbase_dir, 'qnanopainter', '6.8.3', 'aarch64')
        env['LIBS'].append('qnanopainter')
        env['LIBPATH'].append(os.path.join(qnp_base_dir, 'lib'))
        env['CPPPATH'].append(os.path.join(qnp_base_dir, 'include'))

PLATFORM_MAP = [
   {
     'variants':{'opsys':'Linux', 'arch':'aarch64'},
        'result':AndroidTermuxQtLib},
    {
        'variants': {'platform_target': 'wasm_32'},
        'result': WasmST68QtLib
    },
    {
        'variants': {'platform_target': 'ios'},
        'result': IOSQtLib
    },
    {
        'variants': {'opsys': 'Linux'},
        'result': LinuxQtLib
    },
    {
        'variants': {'opsys': 'Windows'},
        'result': WindowsQtLib
    },
    {
        'variants': {'opsys': 'Darwin'},
        'result': DarwinQtLib
    }
]