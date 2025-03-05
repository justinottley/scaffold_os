#
# Copyright 2014-2024 Justin Ottley
#
# Licensed under the terms set forth in the LICENSE.txt file
#

import os
import json
import argparse
from collections import OrderedDict

import scaffold.variant

from .benv import BuildEnvironment

from . import globals as buildsys_globals
from . import buildtype
from . import buildlib

from .. import gitutil

sc_globals = argparse.Namespace()


class ScNinjaNode:

    def __init__(self, parent, reldir):
        self.__parent = parent
        self.__reldir = reldir

        benv = BuildEnvironment()
        benv.node = self
        benv.inherit(parent.benv)

        self.sset_node = False

        self.__ninja_build = ''
        self.__node_ninja_build = ''
        self.__build_environment = benv

        self.build_nodes = []

    def _set_ninja_build(self, build_rules):
        
        # accumulate build rules for this node only
        self.__node_ninja_build = build_rules

        if self.sset_node:
            self.__ninja_build = build_rules
        else:

            # accumulate all build rules to top-level software set
            self.parent.ninja_build = build_rules

    def _get_ninja_build(self):
        if self.sset_node:
            return self.__ninja_build
        else:
            return self.parent.ninja_build

    ninja_build = property(_get_ninja_build, _set_ninja_build)


    def _get_node_ninja_build(self):
        return self.__node_ninja_build

    def _set_node_ninja_build(self, build_rules):
        self.__node_ninja_build = build_rules

    node_ninja_build = property(_get_node_ninja_build, _set_node_ninja_build)


    @property
    def parent(self):
        return self.__parent

    @property
    def reldir(self):
        return self.__reldir

    @property
    def relpath(self):
        return os.path.join(self.parent.reldir, self.reldir)

    @property
    def benv(self):
        return self.__build_environment

    def _export(self, key, value):
        self.benv.exports[key] = value

    def _subdir(self, subdir):
        node = ScNinjaNode(self, subdir)
        script_path = 'ScaffoldScript'
        node.run(script_path)

    def _build(self, subdir):
        node = ScNinjaNode(self, subdir)
        script_path = 'ScaffoldScript'
        nnode = node.run(script_path)

        if not nnode:
            return

        btype_mod = buildtype.get_buildtype_lib(
            nnode.benv.build_type)

        btype_mod.configure_env(nnode.benv)
        btype_mod.configure_builders(nnode.benv)

        # accumulate build rules
        #
        node_ninja_build = nnode.benv.gen_build()
        self.ninja_build += node_ninja_build

        nnode.node_ninja_build += node_ninja_build
        self.build_nodes.append(nnode)



    def _init_sset(self, sset_name, sset_config=None):
        sset_config = sset_config or {}
        if 'sset_name' in self.benv.interface:
            raise Exception('nested software set found - {} {}'.format(
                self.benv.sset_name,
                sset_name
            ))
        self.sset_node = True
        self.benv.sset_name = sset_name
        self.benv.sset_rname = '{}{}'.format(
            buildsys_globals.senv_config['site_name'].capitalize(),
            sset_name.capitalize()
        )
        self.benv.sset_dir = self.reldir
        self.benv.sset_inst_dir = os.path.join(self.benv.inst_top_dir, sset_name)

        sset_config.update({
            'projects': {},
            'sftset_type': 'int', # internal
            'sftset_src_relpath': self.reldir
        })

        sc_globals.sc_config[sset_name] = sset_config


    def _init_product_name(self, product_name):
        self.benv.product_name = product_name
        self.benv.product_dir = self.reldir

        proj_config = {}
        if sc_globals.gen_config:
            
            if self.sset_node:
                sset_src_relpath = sc_globals.sc_config[self.benv.sset_name]['sftset_src_relpath']
                sc_globals.sc_config[self.benv.sset_name]['sftset_src_relpath'] = os.path.dirname(sset_src_relpath)

            proj_src_relpath = os.path.dirname(self.reldir.replace(self.benv.sset_dir, ''))
            if proj_src_relpath == '/':
                proj_src_relpath = ''
    
            proj_config['project_src_relpath'] = proj_src_relpath
            proj_config['git_url'] = gitutil.get_url(path=self.reldir)
            proj_config['git_branch'] = gitutil.get_branch(path=self.reldir)

            repo_top = gitutil.get_repo_dirname(proj_config['git_url'])
            if repo_top != product_name:
                proj_config['project_dirname'] = product_name

            sc_globals.sc_config[self.benv.sset_name]['projects'][product_name] = proj_config

        self.benv.product_config = proj_config


    def _install_products(self, sset_name):
        pass

    @property
    def node_locals(self):
        return {
            'Export': self._export,
            'Subdir': self._subdir,
            'Build': self._build,
            'Product': self._init_product_name,
            'SoftwareSet': self._init_sset,
            'SoftwareSetInstallProducts': self._install_products,
            'benv': self.benv,
            'ScConfig': sc_globals.sc_config
        }


    def run(self, script_path):

        script_path = script_path.strip()
        node = ScNinjaNode(self, self.relpath)
        script_path = os.path.join(self.relpath, script_path)

        platform_target = scaffold.variant.get_variant('platform_target')

        if os.path.isfile(script_path):
            with open(script_path) as fh:

                print('Node: execing: {}'.format(script_path))
                contents = fh.read()
                exec(contents, node.node_locals)

            if node.sset_node:
                print('GOT SSET NODE AT {}'.format(script_path))
                bninja_path = 'build/gen/{}/build_{}.ninja'.format(
                    platform_target, node.benv.sset_name)
                with open(bninja_path, 'w') as wfh:
                    wfh.write(node.ninja_build)

                print('Wrote {}'.format(bninja_path))

            if node.build_nodes:
                for bnode in node.build_nodes:

                    nninja_path = ''
                    if bnode.benv.build_type == 'shared_library':
                        nninja_path = 'build/gen/{}/build_{}.{}.ninja'.format(
                            platform_target, bnode.benv.sset_name, bnode.benv.lib_name
                        )

                    elif bnode.benv.build_type == 'binary_executable':
                        nninja_path = 'build/gen/{}/build_{}.{}.ninja'.format(
                            platform_target, bnode.benv.sset_name, bnode.benv.executable_name
                        )

                    elif bnode.benv.build_type == 'python_package':
                        nninja_path = 'build/gen/{}/build_{}.py.ninja'.format(
                            platform_target, bnode.benv.sset_name
                        )

                    if nninja_path:
                        with open(nninja_path, 'w') as wfh:
                            wfh.write(bnode.node_ninja_build)

                        print('Wrote {}'.format(nninja_path))

            return node

        else:
            print('Node: Error: file not found: {}'.format(script_path))

class ScNinjaRuntime(object):

    def __init__(self, gen_config=False):

        global sc_globals

        # Generate sc_config.json build description
        sc_globals.gen_config = gen_config
        sc_globals.sc_config = OrderedDict()
        sc_globals.sc_config['__bootstrap__'] = {
            'buildsys.inst_dir': os.path.abspath(self.buildsys_inst_dir),
            'export_env': {}
        }

        self.benv = BuildEnvironment()
        self.benv.root_dir = os.path.abspath('.')
        self.ninja_build = 'include rules.ninja\n\n'

    @property
    def relpath(self):
        return ''

    @property
    def reldir(self):
        return ''

    @property
    def buildsys_inst_dir(self):
        platform_target = scaffold.variant.get_variant('platform_target')
        return os.path.join('inst', platform_target)


    def run(self, script_path):

        node = ScNinjaNode(self, '')

        with open(script_path) as fh:

            print('execing: {}'.format(script_path))
            contents = fh.read()
            exec(contents, node.node_locals)
        
        # write the build time for use by dist
        if os.getenv('SCAFFOLD_BUILD_TIME') != '0':
            build_time_path = os.path.join(self.buildsys_inst_dir, '.build_time')
            with open(build_time_path, 'w') as wfh:
                wfh.write(str(buildsys_globals.build_time))

            print('Wrote Build Time: {} to {}'.format(
                buildsys_globals.build_time, build_time_path
            ))

        # Write list of software sets

        if sc_globals.gen_config:
            sc_config_path = os.path.join(self.buildsys_inst_dir, 'sc_config.json')
            
            with open(sc_config_path, 'w') as wfh:
                wfh.write(json.dumps(sc_globals.sc_config, indent=2))

            print('Wrote {}'.format(sc_config_path))

        if not buildsys_globals._RULES_DONE: # no rules written, generate empty

            bl_opsys = buildlib.get_lib('OpSys')
            b_ch = bl_opsys.builder('CopyHeaders') # actuall just for install_files rule
            b_ch_obj = b_ch(node.benv)

            rules_path = 'build/gen/{}/rules.ninja'.format(
                scaffold.variant.get_variant('platform_target'))

            with open(rules_path, 'w') as wfh:
                wfh.write(b_ch_obj.gen_rules())

            print('Wrote {}'.format(rules_path))

        print('')
        print('DONE')
