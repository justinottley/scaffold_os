
import os
import json
import base64
import platform

from .. import ThirdbaseLib, Builder

from ... import util as buildsys_util
import scaffold.buildsys.globals as buildsys_globals

pyver_parts = platform.python_version_tuple()
PYVER = 'python{}:{}'.format(pyver_parts[0], pyver_parts[1])

class PB11GeneratorBuilder(Builder):

    def __init__(self, *args, **kwargs):
        Builder.__init__(self, *args, **kwargs)

        _outputs = self.outputs
        if _outputs:
            self.benv.cpps.append(_outputs[2])
            self.benv.cpps.append(_outputs[3])

    @property
    def outputs(self):
        
        if 'pybind11_info' not in self.benv.interface:
            return []

        lib_include_dir = os.path.join(self.benv.sset_inst_dir, 'include', self.benv.sset_rname, self.benv.lib_name)

        o_header = os.path.join(lib_include_dir, 'pymodule.h')
        o_ssc = os.path.join(lib_include_dir, 'pysigslot.h')
        o_ssc_cpp = os.path.join(lib_include_dir, 'pysigslot.cpp')
        o_cpp = os.path.join(self.benv.sset_gen_lib_dir, 'pymodule.cpp')
        
        return [o_header, o_ssc, o_ssc_cpp, o_cpp]


    def _gen_fn(self):

        fn = '    defines = '
        for define_entry in self.benv.env['CPPDEFINES']:
            fn += ' -D{}'.format(define_entry)

        fn += '\n'
        fn += '    cpppath = '
        for inc_entry in self.benv.env['CPPPATH']:
            fn += ' -I{}'.format(inc_entry)

        fn += '\n'
        fn += '    libpath = -L{}'.format('inst/Linux/{}/lib'.format(self.benv.sset_name))
        for libpath_entry in reversed(self.benv.env['LIBPATH']):
            fn += ' -L{}'.format(libpath_entry)

        fn += '\n'
        fn += '    libs = -l{}{}'.format(self.benv.sset_rname, self.benv.lib_name)

        for lib_entry in reversed(self.benv.env['LIBS']):
            fn += ' -l{}'.format(lib_entry)


        return fn


    def gen_rules(self):
        
        sc_gen_cmd = 'sc_gen_pb11'
        if os.name == 'nt':
            sc_gen_cmd = r'C:\Users\justi\dev\scaffold_root\scninja\src\bin\sc_gen_pb11.bat'

        module_mode = 'dynamic'
        if buildsys_globals.args['pybind_mode'] == 'static':
            module_mode = 'static'


        n  = 'rule gen_pb11\n'
        n += '    command = {} --mode {} --sset_rname $sset_rname --lib_name $lib_name --src_headers $src_headers --pb_info $pb_info --outputs $out --src_jsons $in'.format(
            sc_gen_cmd,
            module_mode
        )
        n += '\n\n'

        return n

    def gen_build(self):

        if 'pybind11_info' not in self.benv.interface:
            return ''

        json_list = []
        for moc_output in self.deps[0].outputs:
            json_list.append('{}.json'.format(moc_output))

        src_in_str = base64.b64encode(json.dumps(self.benv.pybind11_info).encode('utf-8')).decode('utf-8')

        o_header, o_ssc, o_ssc_cpp, o_cpp = self.outputs

        n  = '\n'
        n += 'build {} {} {} {}: gen_pb11 {}\n'.format(o_header, o_ssc, o_ssc_cpp, o_cpp, ' '.join(json_list))
        n += '    sset_rname = {}\n'.format(self.benv.sset_rname)
        n += '    lib_name = {}\n'.format(self.benv.lib_name)
        n += '    src_headers = {}\n'.format(' '.join(self.benv.headers))
        n += '    pb_info = {}\n'.format(src_in_str)


        if buildsys_globals.args['pybind_mode'] == 'dynamic':

            #
            # python extension module loaded at run-time
            #


            pymod_output_filename = '{}{}module.{}'.format(
                self.benv.sset_rname,
                self.benv.lib_name,
                self.benv.env['SHLIBSUFFIX']
            )
            pymod_output_path = os.path.join(self.benv.shlib_inst_dir, PYVER, 'site-packages', pymod_output_filename)
            pymod_inputs = []
            for entry in ['pysigslot', 'pymodule']:
                pymod_inputs.append('{}/{}.os'.format(self.benv.sset_gen_lib_dir, entry))


            # build shlib output name to depend on it
            #
            shlib_output_filename = 'lib{}{}.{}'.format(
                self.benv.sset_rname,
                self.benv.lib_name,
                self.benv.env['SHLIBSUFFIX']
            )
            shlib_output_path = os.path.join(self.benv.shlib_inst_dir, shlib_output_filename)


            n += '\n'
            n += 'build {}: cxx_lib {} | {}\n'.format(pymod_output_path, ' '.join(pymod_inputs), shlib_output_path)
            n += '    cc_extra_flags = -shared -Wl,--no-as-needed {}\n'.format(self.benv.env['CC_EXTRA_FLAGS'])
            n += self._gen_fn()
            n += '\n'


        return n


class PyBind11Lib(ThirdbaseLib):
    
    BUILDERS =  {
        'PB11Gen': PB11GeneratorBuilder
    }

    def _GetRootDir(self, thirdparty_libs):
        version = buildsys_util.get_required_thirdparty_version(
            thirdparty_libs, 'PyBind11')

        base_dir = os.path.join(self.thirdbase_dir, 'PyBind11', version)

        return (base_dir, version)

    def init(self, benv):

        base_dir, version = self._GetRootDir(benv.required_thirdparty_libs)

        env = benv.env
        env['CPPPATH'].extend([os.path.join(base_dir, 'include')])



PLATFORM_MAP = [
    {
        'variants': {'opsys': 'Linux'},
        'result': PyBind11Lib
    },
    {
        'variants': {'opsys': 'Windows'},
        'result': PyBind11Lib
    },
    {
        'variants': {'opsys': 'Darwin'},
        'result': PyBind11Lib
    }
]
