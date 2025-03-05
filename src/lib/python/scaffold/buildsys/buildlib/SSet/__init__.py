
import os

from .. import BuildlibBase, Builder
from ... import globals as buildsys_globals

def get_lib_info(benv):

    if 'required_libs' not in benv.interface:
        return

    lib_paths = set()
    inc_paths = set()
    libs = [] # preserve order
    lib_fullpaths = set()
    defines = set()

    sset_feature_define = 'REVLENS_SSET_{}'.format(benv.sset_name.upper())
    defines.add(sset_feature_define)

    # required_libs - libs internal to this product
    #
    for required_lib in benv.required_libs.split():
        required_lib = required_lib.strip()
        required_lib_parts = required_lib.split('.')

        sset_name, lib_name = required_lib_parts

        sset_dir = os.path.join(benv.inst_top_dir, sset_name)

        sset_lib_path = os.path.join(sset_dir, 'lib')
        sset_inc_path = os.path.join(sset_dir, 'include')

        lib_paths.add(sset_lib_path)
        inc_paths.add(sset_inc_path)

        shlib_name = '{}{}{}'.format(
            buildsys_globals.senv_config['site_name'].capitalize(),
            sset_name.capitalize(),
            lib_name
        )
        if shlib_name not in libs:
            libs.append(shlib_name)

        lib_prefix = 'lib'
        if os.name == 'nt':
            lib_prefix = ''
        lib_fullpath = os.path.join(sset_lib_path, '{}{}.{}'.format(
            lib_prefix, shlib_name, benv.env['SHLIBSUFFIX']))
        lib_fullpaths.add(lib_fullpath)


        # for DECL_IMPORT / DECL_EXPORT handling
        #
        lib_define = '{cn}_{l}_LIB'.format(
            cn=sset_name.upper(),
            l=lib_name.upper()
        )

        defines.add(lib_define)


    return (defines, lib_paths, inc_paths, libs, lib_fullpaths)


class InstallProductsBuilder(Builder):

    def gen_rules(self):

        n  = 'rule install_products\n'
        n += '    command = sc_install_products $in $out'

        return n

    def gen_build(self):
        n  = '\n'
        n += 'build {}: install_products {}\n\n'.format(

        )

class DependentLibsBuilder(Builder):

    @property
    def outputs(self):

        result = get_lib_info(self.benv)
        if result:
            _, _, _, _, lib_fullpaths = get_lib_info(self.benv)
            result = list(lib_fullpaths)
            return result

        return []


    def gen_rules(self):
        return ''


    def gen_build(self):
        return ''


class SoftwareSetLib(BuildlibBase):

    BUILDERS = {
        'DependentLibs': DependentLibsBuilder,
        'InstallProducts': InstallProductsBuilder
    }

    def init(self, benv):

        env = benv.env

        # include the sset include dir that corresponds to this product, if no
        # required_libs are specified
        env['CPPPATH'].append(os.path.join(benv.sset_inst_dir, 'include'))

        result = get_lib_info(benv)
        if result:
            defines, lib_paths, inc_paths, libs, _ = result
            
            env['CPPPATH'].extend(list(inc_paths))
            env['LIBPATH'].extend(list(lib_paths))
            env['LIBS'].extend(list(libs))
            env['CPPDEFINES'].extend(defines)



PLATFORM_MAP = [
    {
        'variants': {},
        'result': SoftwareSetLib
    }
]