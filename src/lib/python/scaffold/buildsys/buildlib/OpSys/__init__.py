
import os
import time
import platform

import scaffold.variant

from .. import BuildlibBase, Builder, ThirdbaseLib
from ... import globals as buildsys_globals


SCAFFOLD_BUILD_TIME = int(time.time())
if os.getenv('SCAFFOLD_BUILD_TIME'):
    SCAFFOLD_BUILD_TIME = int(os.getenv('SCAFFOLD_BUILD_TIME'))

buildsys_globals.build_time = SCAFFOLD_BUILD_TIME

class CompileBuilder(Builder):

    def _gen_fn(self):

        fn = '    defines = '
        for define_entry in self.benv.env['CPPDEFINES']:
            fn += ' -D{}'.format(define_entry)

        fn += '\n'
        fn += '    cpppath = '
        for inc_entry in self.benv.env['CPPPATH']:
            fn += ' -I{}'.format(inc_entry)

        # wasm / emscripten / ios
        for isystem_entry in self.benv.env.get('ISYSTEMPATH', []):
            fn += ' -isystem {}'.format(isystem_entry)

        fn += '\n'
        fn += '    libpath = '
        for libpath_entry in reversed(self.benv.env['LIBPATH']):
            fn += ' -L{}'.format(libpath_entry)

        fn += '\n'
        fn += '    libs = '

        for lib_entry in reversed(self.benv.env['LIBS']):
            fn += ' -l{}'.format(lib_entry)


        return fn


    def gen_rules(self):

        env = self.benv.env

        # TODO FIXME HACK
        #
        if buildsys_globals._RULES_DONE:
            return ''


        n  = 'rule cxx\n'
        n += '    command = {} -o $out $cc_extra_flags {} $defines $cpppath $libpath $libs -c $in'.format(
            env['CXX'], env['CXXFLAGS'])

        n += '\n\n'

        n += 'rule cxx_lib\n'
        n += '    command = {} -o $out $cc_extra_flags {} $defines $cpppath $libpath $libs $in'.format(
            env['CXX_LIB'], env['CXX_LIB_FLAGS'])

        n += '\n\n'
        n += 'rule cxx_exec\n'
        n += '    command = {} {} -o $out $linkflags $in $cc_extra_flags {} $defines $cpppath $libpath $libs\n\n'.format(
            env['CXX'],
            env.get('CXX_PRE_OUT_FLAGS', ''),
            env['CXXFLAGS']
        )

        n += 'rule cc\n'
        n += '    command = {} -o $out $cc_extra_flags {} $in\n\n'.format(
            env['CC'], env['CCFLAGS']
        )

        buildsys_globals._RULES_DONE = True

        return n


class WindowsCompileBuilder(CompileBuilder):

    def _gen_fn(self):

        fn = '    defines = '
        for define_entry in self.benv.env['CPPDEFINES']:
            fn += ' /D{}'.format(define_entry)

        fn += '\n'
        fn += '    cpppath = '
        for inc_entry in self.benv.env['CPPPATH']:
            fn += ' /I{}'.format(inc_entry)

        return fn


    def gen_rules(self):

        # TODO FIXME HACK
        #
        if buildsys_globals._RULES_DONE:
            return ''


        env = self.benv.env

        n  = 'rule cxx\n'
        n += '    command = {} /Fo$out /c $in $cc_extra_flags {} $defines $cpppath $libpath $libs'.format(
            env['CXX'], env['CXXFLAGS'])

        n += '\n\n'

        n += 'rule cxx_lib\n'
        n += '    command = {} $cc_extra_flags /out:$out /implib:$implib {} $defines $cpppath $libpath $libs $in'.format(
            env['CXX_LIB'], env['CXX_LIB_FLAGS'])

        n += '\n\n'
        n += 'rule cxx_exec\n'
        n += '    command = {} /OUT:$out $linkflags $cc_extra_flags {} $defines $cpppath $libpath $libs $in\n\n'.format(
            env['CXX_LIB'], env['CXX_EXEC_FLAGS']
        )

        n += 'rule cc\n'
        n += '    command = {} /Fo$out /c $in $cc_extra_flags {} $cpppath\n\n'.format(
            env['CC'], env['CCFLAGS']
        )

        buildsys_globals._RULES_DONE = True

        return n



class ObjectBuilder(CompileBuilder):

    def __init__(self, *args, **kwargs):
        CompileBuilder.__init__(self, *args, **kwargs)

        if 'cpp_classes' in self.benv.interface:
            self.benv.env['CCEXT'] = '.cpp'
            self.benv.env['OBJEXT'] = '.os'

        elif 'cpp_files' in self.benv.interface:
            self.benv.env['CCEXT'] = '.cpp'
            self.benv.env['OBJEXT'] = '.o'

        elif 'c_files' in self.benv.interface:
            self.benv.env['CCEXT'] = '.c'
            self.benv.env['OBJEXT'] = '.o'



    def _get_object_path(self, cpp_entry):
       
       cpp_entry = cpp_entry.replace(self.benv.env['CCEXT'], self.benv.env['OBJEXT'])
       cpp_entry = cpp_entry.replace('.c', '.obj')
       return os.path.join(
            self.benv.sset_gen_lib_dir,
            os.path.basename(cpp_entry)
        )

    @property
    def input_list(self):

        result = []
        if 'cpp_classes' in self.benv.interface:
            result.extend(self.benv.cpps)

        if 'c_files' in self.benv.interface:
            cresult = []
            for c_entry in self.benv.c_files.split():
                cresult.append(os.path.join(self.benv.node.reldir, c_entry.strip()))

            result.extend(cresult)

        if 'cpp_files' in self.benv.interface:
            cppresult = []
            for cpp_entry in self.benv.cpp_files.split():
                cppresult.append(cpp_entry.strip())

            result.extend(cppresult)

        return result



    @property
    def outputs(self):
        os_list = []
        for cpp_entry in self.input_list:

            if buildsys_globals.args['pybind_mode'] == 'dynamic':
                if 'pymodule' in cpp_entry or 'pysigslot' in cpp_entry:
                    continue

            os_list.append(self._get_object_path(cpp_entry))

        return os_list


    def gen_build(self):

        if not os.path.isdir(self.benv.sset_gen_lib_dir):
            print('Creating {}'.format(self.benv.sset_gen_lib_dir))

        fn = self._gen_fn()

        n = '\n'

        if 'cpp_classes' in self.benv.interface:

            for cpp_entry in self.benv.cpps:
                obj_relpath = self._get_object_path(cpp_entry)

                n += '\n\n'
                n += 'build {}: cxx {}'.format(obj_relpath, cpp_entry)

                dn = ''
                for dep_entry in self.deps:
                    if dep_entry.outputs:
                        dn += ' '.join(dep_entry.outputs)

                    dn += ' '

                if dn:
                    n = '{} | {}'.format(n, dn)

                n += '\n'
                n += '    cc_extra_flags = {}'.format(self.benv.env.get('CC_EXTRA_FLAGS'))
                n += '\n'
                n += fn

        if 'c_files' in self.benv.interface:

            c_file_list = self.benv.c_files.split()
            for c_file in c_file_list:
                c_file = os.path.join(self.benv.node.reldir, c_file.strip())
                obj_relpath = self._get_object_path(c_file)
                n += '\n\n'
                n += 'build {}: cc {}\n'.format(obj_relpath, c_file)
                n += '    cc_extra_flags = -c\n'

        if 'cpp_files' in self.benv.interface:

            cpp_file_list = self.benv.cpp_files.split()
            for cpp_file in cpp_file_list:
                cpp_file = os.path.join(self.benv.node.reldir, cpp_file.strip())

                exec_path = self._get_object_path(cpp_file)

                n += '\n\n'
                n += 'build {}: cxx {}'.format(exec_path, cpp_file)

                dn = ''
                for dep_entry in self.deps:
                    if dep_entry.outputs:
                        dn += ' '.join(dep_entry.outputs)

                    dn += ' '

                if dn:
                    n = '{} | {}'.format(n, dn)

                n += '\n'
                n += '    cc_extra_flags = {}\n'.format(self.benv.env.get('CC_EXTRA_FLAGS'))
                n += fn

        n += '\n'

        return n


class WindowsObjectBuilder(WindowsCompileBuilder):

    def __init__(self, *args, **kwargs):
        WindowsCompileBuilder.__init__(self, *args, **kwargs)

        if 'cpp_classes' in self.benv.interface:
            self.benv.env['CCEXT'] = '.cpp'
            self.benv.env['OBJEXT'] = '.obj'

        elif 'cpp_files' in self.benv.interface:
            self.benv.env['CCEXT'] = '.cpp'
            self.benv.env['OBJEXT'] = '.obj'

        elif 'c_files' in self.benv.interface:
            self.benv.env['CCEXT'] = '.c'
            self.benv.env['OBJEXT'] = '.o'


    def _get_object_path(self, cpp_entry):
       
       cpp_entry = cpp_entry.replace(self.benv.env['CCEXT'], self.benv.env['OBJEXT'])
       cpp_entry = cpp_entry.replace('.c', '.obj')
       return os.path.join(
            self.benv.sset_gen_lib_dir,
            os.path.basename(cpp_entry)
        )
       

    @property
    def input_list(self):

        result = []
        if 'cpp_classes' in self.benv.interface:
            result.extend(self.benv.cpps)

        if 'c_files' in self.benv.interface:
            cresult = []
            for c_entry in self.benv.c_files.split():
                cresult.append(os.path.join(self.benv.node.reldir, c_entry.strip()))

            result.extend(cresult)

        if 'cpp_files' in self.benv.interface:
            cppresult = []
            for cpp_entry in self.benv.cpp_files.split():
                cppresult.append(cpp_entry.strip())

            result.extend(cppresult)

        return result



    @property
    def outputs(self):
        os_list = []
        for cpp_entry in self.input_list:
            os_list.append(self._get_object_path(cpp_entry))

        return os_list


    def gen_build(self):

        if not os.path.isdir(self.benv.sset_gen_lib_dir):
            print('Creating {}'.format(self.benv.sset_gen_lib_dir))

        fn = self._gen_fn()

        n = '\n'

        if 'cpp_classes' in self.benv.interface:

            for cpp_entry in self.benv.cpps:
                obj_relpath = self._get_object_path(cpp_entry)

                n += '\n\n'
                n += 'build {}: cxx {}'.format(obj_relpath, cpp_entry)

                dn = ''
                for dep_entry in self.deps:
                    if dep_entry.outputs:
                        dn += ' '.join(dep_entry.outputs)

                    dn += ' '

                if dn:
                    n = '{} | {}'.format(n, dn)

                n += '\n'
                n += '    cc_extra_flags = \n'
                # n += '\n'
                n += fn

        if 'c_files' in self.benv.interface:
            
            win_cpppath = ''
            for inc_entry in self.benv.env['CPPPATH']:
                win_cpppath += ' /I{}'.format(inc_entry)

            c_file_list = self.benv.c_files.split()
            for c_file in c_file_list:
                c_file = os.path.join(self.benv.node.reldir, c_file.strip())
                obj_relpath = self._get_object_path(c_file)
                n += '\n\n'
                n += 'build {}: cc {}\n'.format(obj_relpath, c_file)
                n += '    cc_extra_flags = \n'
                n += '    cpppath = {}\n'.format(win_cpppath)
                n += '    '


        if 'cpp_files' in self.benv.interface:

            cpp_file_list = self.benv.cpp_files.split()
            for cpp_file in cpp_file_list:
                cpp_file = os.path.join(self.benv.node.reldir, cpp_file.strip())

                exec_path = self._get_object_path(cpp_file)

                n += '\n\n'
                n += 'build {}: cxx {}'.format(exec_path, cpp_file)

                dn = ''
                for dep_entry in self.deps:
                    if dep_entry.outputs:
                        dn += ' '.join(dep_entry.outputs)

                    dn += ' '

                if dn:
                    n = '{} | {}'.format(n, dn)

                n += '\n'
                n += '    cc_extra_flags = \n'
                n += fn

        n += '\n'

        return n

class DarwinObjectBuilder(ObjectBuilder):

    def _gen_fn(self):

        fn = '    defines = '
        for define_entry in self.benv.env['CPPDEFINES']:
            fn += ' -D{}'.format(define_entry)

        fn += '\n'
        fn += '    cpppath = '
        for inc_entry in self.benv.env['CPPPATH']:
            fn += ' -I{}'.format(inc_entry)

        # ios
        if self.benv.env.get('ISYSTEMPATH'):
            for isystem_entry in self.benv.env.get('ISYSTEMPATH', []):
                fn += ' -isystem {}'.format(isystem_entry)


        fn += '\n'
        fn += '    libpath = '
        for libpath_entry in reversed(self.benv.env['LIBPATH']):
            fn += ' -L{}'.format(libpath_entry)

        fn += '\n'

        fn += '    libs = '
        for fworkpath_entry in reversed(self.benv.env['FRAMEWORKPATH']):
            fn += ' -F{}'.format(fworkpath_entry)

        if self.benv.env.get('FRAMEWORKS'):
            for lib_entry in reversed(self.benv.env['FRAMEWORKS']):
                fn += ' -framework {}'.format(lib_entry)
        
        if self.benv.env.get('LIBS'):
            for lib_entry in self.benv.env['LIBS']:
                fn += ' -l{}'.format(lib_entry)

        return fn


class IOSObjectBuilder(DarwinObjectBuilder):

    def gen_rules(self):

        # TODO FIXME HACK
        #
        if buildsys_globals._RULES_DONE:
            return ''


        env = self.benv.env

        n  = 'rule cxx\n'
        n += '    command = {} {} $defines $cpppath $libpath $libs -c $in -o $out'.format(
            env['CXX'], env['CXXFLAGS'])

        n += '\n\n'

        n += 'rule cxx_lib\n'
        n += '    command = {} {} -o $out $in'.format(
            env['CXX_LIB'], env['CXX_LIB_FLAGS'])

        n += '\n\n'
        n += 'rule cxx_exec\n'
        n += '    command = {} {} -o $out $linkflags $in $cc_extra_flags {} $defines $cpppath $libpath $libs\n\n'.format(
            env['CXX'],
            env.get('CXX_PRE_OUT_FLAGS', ''),
            env['CXXFLAGS']
        )

        buildsys_globals._RULES_DONE = True

        return n



class SharedLibBuilder(CompileBuilder):

    def gen_build(self):

        os_inputs = ' '.join(self.deps[0].outputs)
        shlib_prefix = self.benv.env.get('SHLIBPREFIX', 'lib')
        if os.name == 'nt':
            shlib_prefix = ''
        shlib_output_filename = '{}{}{}.{}'.format(
            shlib_prefix,
            self.benv.sset_rname,
            self.benv.lib_name,
            self.benv.env['SHLIBSUFFIX']
        )
        shlib_output_path = os.path.join(self.benv.shlib_inst_dir, shlib_output_filename)


        n  = 'build {}: cxx_lib {}\n'.format(shlib_output_path, os_inputs)
        if scaffold.variant.get_variant('platform_target') == 'wasm_32':
            
            emdir = self.benv.env['EMSCRIPTEN_ROOT']
            n += '    cc_extra_flags = --emdir {}\n'.format(emdir)
            n += '    defines = \n'
            n += '    cpppath = \n'
            n += '    libpath = \n'
            n += '    libs = \n'

        elif os.name == 'nt':
            
            libpath_win = ''
            for l_entry in self.benv.env['LIBPATH']:
                libpath_win += ' /LIBPATH:{}'.format(l_entry.replace('/', '\\'))

            libs_win = ''
            for lib_entry in self.benv.env['LIBS']:
                libs_win += ' {}.lib'.format(lib_entry)

            implib_win = shlib_output_path.replace('.dll', '.lib').replace('/', '\\')

            n += '    cc_extra_flags = \n'
            n += '    defines = \n'
            n += '    libpath = {}\n'.format(libpath_win)
            n += '    libs = {}\n'.format(libs_win)
            n += '    implib = {}\n'.format(implib_win)

        elif platform.system() == 'Darwin':

            libpath_mac = ''
            for l_entry in self.benv.env['LIBPATH']:
                libpath_mac += ' -L{}'.format(l_entry)

            for fworkpath_entry in reversed(self.benv.env['FRAMEWORKPATH']):
                libpath_mac += ' -F{}'.format(fworkpath_entry)


            libs_mac = ''
            for lib_entry in self.benv.env['LIBS']:
                libs_mac += ' -l{}'.format(lib_entry)

            for lib_entry in self.benv.env['FRAMEWORKS']:
                libs_mac += ' -framework {}'.format(lib_entry)

            libtype = '-dynamiclib'
            if scaffold.variant.get_variant('platform_target') == 'ios':
                libtype = ''

            n += '    cc_extra_flags = {} {}\n'.format(libtype, self.benv.env['CC_EXTRA_FLAGS'])
            n += '    defines = \n'
            n += '    libpath = {}\n'.format(libpath_mac)
            n += '    libs = {}\n'.format(libs_mac)

        else: # Linux

            n += '    cc_extra_flags = -shared {}\n'.format(self.benv.env['CC_EXTRA_FLAGS'])
            n += self._gen_fn()
            n += '\n'


        n += '\n'

        return n


class CompiledExecutableBuilder(ObjectBuilder):

    def gen_build(self):

        all_sources = self.deps[0].outputs
        if 'qrc_resource_libs' in self.benv.interface:
            
            res_ext = 'os'
            if os.name == 'nt':
                res_ext = 'obj'

            for qrc_lib in self.benv.qrc_resource_libs.split():
                qrc_lib = qrc_lib.strip()
                qrc_lib_parts = qrc_lib.split('.')
                sset_name, lib_name = qrc_lib_parts
                qrc_gen_dir = os.path.join(self.benv.inst_top_dir, sset_name, '_gen', 'lib', lib_name)
                qrc_name = '{}_{}_resources.{}'.format(sset_name, lib_name, res_ext)

                lib_fullpath = os.path.join(qrc_gen_dir, qrc_name)
                all_sources.append(lib_fullpath)

        o_sources = ' '.join(all_sources)

        exec_name = self.benv.executable_name
        if scaffold.variant.get_variant('platform_target') == 'wasm_32':
            exec_name += '.js'

        exec_out_path = os.path.join(self.benv.bin_inst_dir, exec_name)
        if os.name == 'nt':
            
            exec_out_path += '.exe'

            libpath_win = ''
            for l_entry in self.benv.env['LIBPATH']:
                libpath_win += ' /LIBPATH:{}'.format(l_entry.replace('/', '\\'))

            libs_win = ''
            for lib_entry in self.benv.env['LIBS']:
                libs_win += ' {}.lib'.format(lib_entry)


            n = 'build {}: cxx_exec {}\n'.format(exec_out_path, o_sources)
            n += '    cc_extra_flags = \n'
            n += '    defines = \n'
            n += '    libpath = {}\n'.format(libpath_win)
            n += '    libs = {}\n'.format(libs_win)

        else:
            n = 'build {}: cxx_exec {}\n'.format(exec_out_path, o_sources)
            n += '    cc_extra_flags = {}\n'.format(self.benv.env.get('CXX_LINK_FLAGS', ''))
            n += '    linkflags = {}\n'.format(' '.join(self.benv.env['LINKFLAGS']))
            n += self._gen_fn()

        return n

class DarwinCompiledExecutableBuilder(CompiledExecutableBuilder):

    def _gen_fn(self):

        fn = '    defines = '
        for define_entry in self.benv.env['CPPDEFINES']:
            fn += ' -D{}'.format(define_entry)

        fn += '\n'
        fn += '    cpppath = '
        for inc_entry in self.benv.env['CPPPATH']:
            fn += ' -I{}'.format(inc_entry)

        fn += '\n'
        fn += '    libpath = '
        for libpath_entry in reversed(self.benv.env['LIBPATH']):
            fn += ' -L{}'.format(libpath_entry)

        for fworkpath_entry in reversed(self.benv.env['FRAMEWORKPATH']):
            fn += ' -F{}'.format(fworkpath_entry)
        
        fn += '\n'

        fn += '    libs = '

        libs_mac = ''
        for lib_entry in self.benv.env['LIBS']:
            libs_mac += ' -l{}'.format(lib_entry)

        for lib_entry in self.benv.env['FRAMEWORKS']:
            libs_mac += ' -framework {}'.format(lib_entry)

        fn += libs_mac
        fn += '\n'

        return fn


class ScriptExecutableBuilder(Builder):

    @property
    def outputs(self):

        bin_dir = os.path.join(self.benv.sset_inst_dir, 'bin')
        result = []
        for bin_entry in self.benv.bin_files.split():
            result.append(os.path.join(bin_dir, bin_entry.strip()))

        return result


    def gen_build(self):
        
        n = '\n'
        for src_name in self.benv.bin_files.split():
            src_name = src_name.strip()
            src_relpath = os.path.join(self.benv.node.reldir, src_name)

            src_out_name = src_name
            if os.name != 'nt':
                src_out_name = src_name.replace('.py', '')

            dest_relpath = os.path.join(self.benv.sset_inst_dir, 'bin', src_out_name)

            n += 'build {}: install_files {}\n'.format(dest_relpath, src_relpath)
            n += '    itype = direct_exe\n'
            n += '    sset = {}\n'.format(self.benv.sset_rname)
            n += '    lib_name = {}\n'.format(src_out_name)

        n += '\n'

        return n


class CopyHeadersBuilder(Builder):

    @property
    def outputs(self):

        if not self.benv.lib_name:
            return []

        return [os.path.join(
            self.benv.sset_inst_dir,
            'include',
            self.benv.sset_rname,
            self.benv.lib_name.upper(),
            '.contents'
        )]


    def _generate_cmd(self):

        sc_install_cmd = 'sc_install'
        if os.name == 'nt':
            sc_install_cmd = r'C:\Users\justi\dev\scaffold_root\scninja\src\bin\sc_install.bat'
    
        cmd = '{} --itype $itype -s $sset --libname $lib_name --dest $out $in'.format(sc_install_cmd)
        return cmd


    def gen_rules(self):

        n  = 'rule install_files\n'
        n += '    command = {}\n\n'.format(self._generate_cmd())
        
        return n


    def gen_build(self):

        n = '\n'
        if not self.benv.interface.get('lib_name'):
            return n

        all_headers = self.benv.headers
        if 'header_files' in self.benv.interface:
            for header_file in self.benv.header_files.split():
                all_headers.append(os.path.join(self.benv.node.reldir, header_file.strip()))

        n  = '\n'
        n += 'build {}: install_files {}\n'.format(
            self.outputs[0], ' '.join(all_headers))
        n += '    itype = header\n'
        n += '    sset = {}\n'.format(self.benv.sset_rname)
        n += '    lib_name = {}\n'.format(self.benv.lib_name)
        n += '\n'

        return n


class CopyFilesBuilder(Builder):

    def _gen_build(self, sources):

        n = '\n'
        n += 'build {}: install_files {}\n'.format(
            self.outputs[0], ' '.join(sources)
        )
        n += '    itype = subdir\n'
        n += '    sset = {}\n'.format(self.benv.sset_rname)
        n += '    lib_name = {}\n'.format(self.benv.node.reldir)
        n += '\n'

        return n


class CopyPyFilesBuilder(CopyFilesBuilder):

    @property
    def outputs(self):
        contents_path = os.path.join(
            self.benv.sset_inst_dir,
            'lib',
            self.benv.pydir_name,
            'site-packages',
            '.contents_{}'.format(self.benv.product_name)
        )
        return [contents_path]


    def gen_build(self):

        sources = []
        for pypackage_dir in self.benv.python_package_dirs:
            src_dir = os.path.join(self.benv.node.reldir, pypackage_dir)

            for root, dirs, files in os.walk(src_dir):
                for file_entry in files:
                    file_fullpath = os.path.join(root, file_entry)
                    file_relpath = self._get_relpath(file_fullpath)
                    sources.append(file_relpath)

        return self._gen_build(sources)


class CopyStaticFilesBuilder(CopyFilesBuilder):

    @property
    def outputs(self):
        return [
            os.path.join(
                self.benv.sset_inst_dir,
                self.benv.target_dir,
                '.contents_{}'.format(self.benv.product_name)
            )
        ]


    def gen_build(self):

        sources = []
        for entry in self.benv.static_files.split():
            entry_relpath = os.path.join(self.benv.node.reldir, entry.strip())
            sources.append(entry_relpath)

        return self._gen_build(sources)


class OpsysLibBase(BuildlibBase):

    BUILDERS = {
        'Object': ObjectBuilder,
        'SharedLib': SharedLibBuilder,
        'CompiledExecutable': CompiledExecutableBuilder,
        'ScriptExecutable': ScriptExecutableBuilder,
        'CopyHeaders': CopyHeadersBuilder,
        'CopyPyFiles': CopyPyFilesBuilder,
        'CopyStaticFiles': CopyStaticFilesBuilder
    }


class LinuxLib(OpsysLibBase):

    def init(self, benv):

        env = benv.env

        env['SHLIBSUFFIX'] = 'so'

        # CPP compiler
        #
        env['CXX'] = '/usr/bin/g++ '
        env['CXXFLAGS'] = ' -std=c++17 -Wno-attributes -Wno-deprecated-declarations -Wno-deprecated -fPIC '

        env['CXX_LIB'] = env['CXX']
        env['CXX_LIB_FLAGS'] = env['CXXFLAGS']

        # flags that can be supplied by build types
        env['CC_EXTRA_FLAGS'] = ''

        env['LINKFLAGS'] = []

        env['CPPPATH'] = [
            '/usr/include',
            '/usr/include/c++/9',
            '/usr/include/x86_64-linux-gnu/c++/9'
        ]
        
        env['LIBPATH'] = [
            '/usr/lib',
            '/usr/lib/x86_64-linux-gnu'
        ]

        env['LIBS'] = ['stdc++']

        env['CPPDEFINES'] = ['SCAFFOLD_BUILD_TIME={}'.format(SCAFFOLD_BUILD_TIME)]

        if buildsys_globals.args.get('pybind_mode') == 'static':
            env['CPPDEFINES'].append('SCAFFOLD_PYBIND_STATIC')


        # C compiler
        #
        env['CC'] = '/usr/bin/gcc'
        env['CCFLAGS'] = ' -fPIC '


class DarwinLib(LinuxLib):

    BUILDERS = {
        'Object': DarwinObjectBuilder,
        'SharedLib': SharedLibBuilder,
        'CompiledExecutable': DarwinCompiledExecutableBuilder,
        'ScriptExecutable': ScriptExecutableBuilder,
        'CopyHeaders': CopyHeadersBuilder,
        'CopyPyFiles': CopyPyFilesBuilder,
        'CopyStaticFiles': CopyStaticFilesBuilder
    }
    def init(self, benv):
        super(DarwinLib, self).init(benv)

        env = benv.env

        env['SHLIBSUFFIX'] = 'dylib'

        env['CXX'] = '/usr/bin/clang++'
        env['CCFLAGS'] = ' -std=c++17 -fPIC -arch arm64 '
        env['CXXFLAGS'] += ' -arch arm64 -Wno-unused-command-line-argument -Wno-inconsistent-missing-override '
        env['LDFLAGS'] = ' -Wl,--export_dynamic '
        # -isysroot /Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX10.9.sdk -mmacosx-version-min=10.7'
        
        env['CPPPATH'] = []
        env['LIBPATH'] = []
        env['LIBS'] = []
        env['RPATH'] = []
        env['PATH'] = ['/usr/bin',
                       '/bin',
                       '/usr/sbin',
                       '/sbin',
                       '/usr/local/bin']

        env['FRAMEWORKS'] = []
        env['FRAMEWORKPATH'] = []


class IOSLib(DarwinLib):

    BUILDERS = {
        'Object': IOSObjectBuilder,
        'SharedLib': SharedLibBuilder,
        'CompiledExecutable': DarwinCompiledExecutableBuilder,
        'ScriptExecutable': ScriptExecutableBuilder,
        'CopyHeaders': CopyHeadersBuilder,
        'CopyPyFiles': CopyPyFilesBuilder,
        'CopyStaticFiles': CopyStaticFilesBuilder
    }

    def init(self, benv):
        super(IOSLib, self).init(benv)

        env = benv.env

        xc_toolchain_root = '/Applications/Xcode.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain'
        sdk_root = '/Applications/Xcode.app/Contents/Developer/Platforms/iPhoneOS.platform/Developer/SDKs'
        sdk_version = 'iPhoneOS15.0.sdk'
        
        env['CXX'] = os.path.join(xc_toolchain_root, 'usr/bin/clang')
        env['CXX_LIB'] = os.path.join(xc_toolchain_root, 'usr/bin/libtool')

        env['SHLIBSUFFIX'] = 'a'

        sdk_path = os.path.join(sdk_root, sdk_version)
        sdk_all_path = os.path.join(sdk_root, 'iPhoneOS.sdk')


        # cxx_flags_list = [
        #     '-x c++',
        #     '-Wno-documentation-unknown-command',
        #     '-Wno-unknown-warning-option',
        #     '-Wno-unknown-pragmas',
        #     '-nostdinc',
        #     '-nostdinc++',
        #     '-std=gnu++17',
        #     '-fsyntax-only',
        #     '-fmessage-length=0',
        #     '-fdiagnostics-show-note-include-stack',
        #     '-fretain-comments-from-system-headers',
        #     '-fmacro-backtrace-limit=0',
        #     '-ferror-limit=1000',
        #     '-arch arm64',
        #     '-g',
        #     '--target=arm64-apple-ios14.0',
        #     '-isysroot {}'.format(sdk_path)
        # ]
        cxx_flags_list = [
            '-x c++',
            '-target arm64-apple-ios14.0',
            '-fmessage-length\=0',
            '-fdiagnostics-show-note-include-stack',
            '-fmacro-backtrace-limit\=0',
            '-Wno-trigraphs',
            '-fpascal-strings',
            '-O0',
            '-Wno-missing-field-initializers',
            '-Wno-missing-prototypes',
            '-Wno-return-type',
            '-Wno-non-virtual-dtor',
            '-Wno-overloaded-virtual',
            '-Wno-exit-time-destructors',
            '-Wno-missing-braces',
            '-Wparentheses',
            '-Wswitch',
            '-Wno-unused-function',
            '-Wno-unused-label',
            '-Wno-unused-parameter',
            '-Wno-unused-variable',
            '-Wunused-value',
            '-Wno-empty-body',
            '-Wno-uninitialized',
            '-Wno-unknown-pragmas',
            '-Wno-shadow',
            '-Wno-four-char-constants',
            '-Wno-conversion',
            '-Wno-constant-conversion',
            '-Wno-int-conversion',
            '-Wno-bool-conversion',
            '-Wno-enum-conversion',
            '-Wno-float-conversion',
            '-Wno-non-literal-null-conversion',
            '-Wno-objc-literal-conversion',
            '-Wno-shorten-64-to-32', # changed
            '-Wno-newline-eof',
            '-Wno-c++11-extensions',
            '-fstrict-aliasing',
            '-Wdeprecated-declarations',
            '-Winvalid-offsetof',
            '-g',
            '-Wno-sign-conversion',
            '-Wno-infinite-recursion',
            '-Wno-move',
            '-Wno-comma',
            '-Wno-block-capture-autoreleasing',
            '-Wno-strict-prototypes',
            '-Wno-range-loop-analysis',
            '-Wno-semicolon-before-method-body',
            '-std\=gnu++17'
        ]

        cxx_flags_list += [
            '-Wno-unused-command-line-argument',
            '-Wno-inconsistent-missing-override'
        ]

        env['CXXFLAGS'] = ' '.join(cxx_flags_list)


        # ld_flags_list = [
        #     '-target arm64-apple-ios14.0',
        #     '-isysroot /Applications/Xcode.app/Contents/Developer/Platforms/iPhoneOS.platform/Developer/SDKs/iPhoneOS15.0.sdk',
        #     '-Xlinker -rpath -Xlinker @executable_path/Frameworks',
        #     '-dead_strip'
        # ]

        env['CXX_LIB_FLAGS'] = '-static' # ' '.join(ld_flags_list)

        env['FRAMEWORKPATH'].extend([
            os.path.join(sdk_all_path, 'System/Library/Frameworks')
        ])

        env['ISYSTEMPATH'] = [
            os.path.join(sdk_all_path, 'usr/include/c++/v1'),
            os.path.join(sdk_all_path, 'usr/include'),
            os.path.join(xc_toolchain_root, 'usr/include')
        ]

        env['CPPDEFINES'].append('SCAFFOLD_IOS')


class WasmLinuxLib(OpsysLibBase):
    '''
    Threading
    em++ -c -pipe -O3 -std=c++1z -fvisibility=hidden -fvisibility-inlines-hidden -fno-exceptions -s USE_PTHREADS=1 -s PTHREAD_POOL_SIZE=4 -s TOTAL_MEMORY=1GB -Wall -Wextra -Wdate-time -Winconsistent-missing-override -DQT_NO_LINKED_LIST -DQT_NO_FOREACH -DQT_NO_JAVA_STYLE_ITERATORS -DQT_NO_LINKED_LIST -DQT_NO_USING_NAMESPACE -DQT_NO_NARROWING_CONVERSIONS_IN_CONNECT -DQT_BUILD_SCRIPTTOOLS_LIB -DQT_BUILDING_QT -DQT_NO_CAST_TO_ASCII -DQT_ASCII_CAST_WARNINGS -DQT_MOC_COMPAT -DQT_USE_QSTRINGBUILDER -DQT_DEPRECATED_WARNINGS -DQT_DISABLE_DEPRECATED_BEFORE=0x050000 -DQT_DEPRECATED_WARNINGS_SINCE=0x060000 -DQT_NO_EXCEPTIONS -D_LARGEFILE64_SOURCE -D_LARGEFILE_SOURCE -DQT_NO_DEBUG -DQT_CORE_LIB -DQT_WIDGETS_LIB -DQT_GUI_LIB -DQT_SCRIPT_LIB -DQT_CORE_LIB 
    '''

    def init(self, benv):

        env = benv.env

        env['SHLIBSUFFIX'] = 'a'

        env['CPPDEFINES'] = [
            'SCAFFOLD_BUILD_TIME={}'.format(SCAFFOLD_BUILD_TIME),
            'SCAFFOLD_PYBIND_STATIC'
        ]

        if 'LINKFLAGS' not in env:
            env['LINKFLAGS'] = []


        if 'ENV' not in env:
            env['ENV'] = {}
        # From https://chromium.googlesource.com/external/github.com/kripken/emscripten/+/refs/tags/1.36.0/tools/scons/site_scons/site_tools/emscripten/emscripten.py?autodive=0%2F

        # emscripten_base_dir = '/home/justinottley/dev/revlens_root/thirdbase/20_04/Linux-x86_64/Emscripten/emsdk'
        thirdbase_inst_dir = buildsys_globals.senv_config['dir.thirdbase']
        emscripten_base_dir = os.path.join(thirdbase_inst_dir, 'emscripten', 'emsdk')
        em_config = os.path.join(emscripten_base_dir, '.emscripten')

        EMSCRIPTEN_ROOT = None

        if not os.path.isfile(em_config):
            raise Exception('emscripten config not found at {}, aborting'.format(em_config))
            
        os.environ['EM_CONFIG'] = em_config

        em_vars = {}

        with open(em_config, 'r') as fh:
            try:
                exec(fh.read(), {}, em_vars)

            except Exception as e:
                print('Error evaluating {}'.format(em_config))

        # print(em_vars)

        # export emscripten vars to environment (simulate sourcing emsdk_env.sh)
        #
        for key, value in em_vars.items():
            if key in ['os', 'emsdk_path', 'JS_ENGINES']:
                continue

            # print('{}={}'.format(key, value))

            os.environ[key] = value
            env['ENV'][key] = value

        env['ENV']['EM_CONFIG'] = em_config

        env['EM_CONFIG'] = em_config
        env['EMSCRIPTEN_ROOT'] = em_vars['EMSCRIPTEN_ROOT']

        env['CXX'] = os.path.join(em_vars['EMSCRIPTEN_ROOT'], 'em++')
        env['CXXFLAGS'] = ' -g -std=gnu++1z -Wall -Wextra -Wno-unused-command-line-argument -Wno-unused-parameter -Wno-inconsistent-missing-override'

        # multithreaded Qt. Requires SharedArrayBuffer which as of 1/1/2024 doesn't seem to be available on mobile
        # env['CXXFLAGS'] = ' -g -pthread -std=gnu++17 -MD -MT -MF -Wno-unused-command-line-argument -Wno-unused-parameter -Wno-inconsistent-missing-override'

        # lib_cmd = '{} rc'.format(os.path.join(em_vars['EMSCRIPTEN_ROOT'], 'emar'))
        env['CXX_LIB'] = 'sc_wasm_lib' # lib_cmd
        env['CXX_LIB_FLAGS'] = ''

        # flags that can be supplied by build types
        env['CC_EXTRA_FLAGS'] = ''

        env['LINK'] = os.path.join(em_vars['EMSCRIPTEN_ROOT'], 'em++')

        # SHLINK and LDMODULE should use LINK so no
        # need to change them here
        
        env['AR']     = os.path.join(em_vars['EMSCRIPTEN_ROOT'], "emar"    )
        env['RANLIB'] = os.path.join(em_vars['EMSCRIPTEN_ROOT'], "emranlib")

        env['PROGSUFFIX'] = '.js'
        env['SHOBJSUFFIX'] = '.o'

        env['LIBS'] = []
        env['RPATH'] = []

        # env['CCFLAGS'] = '-Os -g4 -std=gnu++11 -s ALLOW_MEMORY_GROWTH=1 -Wall -Wextra '
        # env['CCFLAGS'] = '-Os -g4 -std=gnu++11 -s USE_PTHREADS=1 -s WASM=1 -s PTHREAD_POOL_SIZE=4 -s TOTAL_MEMORY=1GB -Wall -Wextra '
        env['CCFLAGS'] = '-c -pipe -g -Wall -Wextra '
        env['CC'] = os.path.join(em_vars['EMSCRIPTEN_ROOT'], 'emcc')

        env['CPPPATH'] = []
        '''
            '/usr/include',
            '/usr/include/c++/9',
            '/usr/include/x86_64-linux-gnu/c++/9'
        ]
        '''

        env['LIBPATH'] = []
        env['LIBPATH_INTERNAL'] = []

        # env.Append(CPPDEFINES=['SCAFFOLD_WASM'])
        # env.Append(CPPDEFINES=['SCAFFOLD_BUILD_TIME={}'.format(SCAFFOLD_BUILD_TIME)])



class WindowsLib(OpsysLibBase):

    BUILDERS = {
        'Object': WindowsObjectBuilder,
        'SharedLib': SharedLibBuilder,
        'CompiledExecutable': CompiledExecutableBuilder,
        'ScriptExecutable': ScriptExecutableBuilder,
        'CopyHeaders': CopyHeadersBuilder,
        'CopyPyFiles': CopyPyFilesBuilder,
        'CopyStaticFiles': CopyStaticFilesBuilder
    }


    def init(self, benv):

        env = benv.env


        # Qt5
        # env['CCFLAGS'] = ' -nologo -Zc:wchar_t -FS -Zc:rvalueCast -Zc:inline -Zc:strictStrings -Zc:throwingNew -Zc:referenceBinding -Zc:__cplusplus -Zi -MDd -W3 -EHsc'
        #
        env['CXXFLAGS'] = ' /FS /nologo /DWIN32 /D_WINDOWS /GR /EHsc /Zi /Ob0 /Od /RTC1 -MDd -Zc:__cplusplus -permissive- -utf-8 -std:c++17'

        #  -w34100 -w34189 -w44996 -w44456 -w44457 -w44458 -wd4577 -wd4467 
        env['CXX'] = 'cl.exe'

        env['CXX_LIB'] = 'link'
        env['CXX_LIB_FLAGS'] = ' /nologo /dll '

        env['CXX_EXEC_FLAGS'] = ' /nologo '

        env['SHLIBSUFFIX'] = 'dll'

        env['CC'] = 'cl.exe'
        env['CCFLAGS'] = env['CXXFLAGS']

        env['LINK'] = 'link'

        # flags that can be supplied by build types
        env['CC_EXTRA_FLAGS'] = ''

        env['LINKFLAGS'] = ['/nologo', '/dll']


        env['CPPPATH'] = []
        env['LIBPATH'] = []
        env['LIBS'] = ['winmm', 'advapi32']
        env['RPATH'] = []
        env['PATH'] = [
            r'C:\Program Files (x86)\Microsoft Visual Studio\2019\BuildTools\VC\Tools\MSVC\14.29.30133\bin\HostX64\x64',
            r'C:\Program Files (x86)\Microsoft Visual Studio\2019\BuildTools\Common7\IDE\VC\VCPackages',
            r'C:\Program Files (x86)\Microsoft Visual Studio\2019\BuildTools\MSBuild\Current\bin\Roslyn',
            r'C:\Program Files (x86)\Windows Kits\10\bin\10.0.18362.0\x86',
            r'C:\Program Files (x86)\Windows Kits\10\bin\x86',
            r'C:\Program Files (x86)\Microsoft Visual Studio\2019\BuildTools\\MSBuild\Current\Bin',
            r'C:\Windows\Microsoft.NET\Framework\v4.0.30319',
            r'C:\Program Files (x86)\Microsoft Visual Studio\2019\BuildTools\Common7\IDE',
            r'C:\Program Files (x86)\Microsoft Visual Studio\2019\BuildTools\Common7\Tools',
            r'C:\Windows\system32;C:\Windows;C:\Windows\System32\Wbem;C:\Windows\System32\WindowsPowerShell\v1.0;C:\Windows\System32\OpenSSH',
            r'C:\Users\justi\AppData\Local\Microsoft\WindowsApps'
        ]
            
        # TODO FIXME: configuration per installation for Git version / path and Python version / path
        #
        r'''
        env['PATH'].extend([
            'C:\Users\justi\dev\revlens_root\thirdbase\20_04\Windows-AMD64-10\Git\2.26.2\Git\cmd',
            'C:\Users\justi\dev\revlens_root\thirdbase\20_04\Windows-AMD64-10\Python\3.7.7\Scripts',
            'C:\Users\justi\dev\revlens_root\thirdbase\20_04\Windows-AMD64-10\Python\3.7.7'
        ])
        '''
        env['CPPDEFINES'] = ['SCAFFOLD_BUILD_TIME={}'.format(SCAFFOLD_BUILD_TIME)]

class AndroidTermuxLinuxLib(LinuxLib):
    def init(self, benv):
      
        env = benv.env
        prefix = os.getenv('PREFIX')
        
        
        env['CXX'] = os.path.join(prefix, 'bin', 'g++')
        env['CXX_LIB'] = env['CXX']
        env['CXXFLAGS'] = '-fPIC -Wno-unused-command-line-argument -Wno-inconsistent-missing-override'
        
        env['CXX_LIB_FLAGS'] = env['CXXFLAGS']

        # flags that can be supplied by build types
        env['CC_EXTRA_FLAGS'] = ''
        
        # C compiler
        #
        env['CC'] = '/usr/bin/gcc'
        env['CCFLAGS'] = ' -fPIC '
        
        env['LIBS'] = ['stdc++']
        env['PATH'] = [
            prefix + '/bin',
        ]
        env['CPPPATH'] = [
            prefix + '/include',
            prefix + '/include/c++/v1'
        ]
        
        env['CPPDEFINES'] = ['SCAFFOLD_BUILD_TIME={}'.format(SCAFFOLD_BUILD_TIME)]
  
        env['LIBPATH'] = []
        env['RPATH'] = []
        env['LINKFLAGS'] = []
        
        env['SHLIBSUFFIX'] = 'so'
        
  

PLATFORM_MAP = [
{'variants':{'opsys':'Linux', 'arch':'aarch64'},
  'result':AndroidTermuxLinuxLib
},
{
    'variants': {'platform_target': 'wasm_32'},
    'result': WasmLinuxLib
},
{
    'variants': {'platform_target': 'ios'},
    'result': IOSLib
},
{
    'variants': {'opsys':'Linux'},
    'result': LinuxLib
},
{
    'variants': {'opsys': 'Windows'},
    'result': WindowsLib
},
{
    'variants': {'opsys': 'Darwin'},
    'result': DarwinLib
}
]