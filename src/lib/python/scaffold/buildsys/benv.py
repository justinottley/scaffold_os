#
# Copyright 2014-2024 Justin Ottley
#
# Licensed under the terms set forth in the LICENSE.txt file
#

import sys

import scaffold.variant

class BuildEnvironment(object):

    def __init__(self):
        self.__env = {}
        self.__interface = {}
        self.__builders = []
        self.__exports = {}

        self._init_defaults()

    @property
    def env(self):
        return self.__env
    
    @property
    def exports(self):
        return self.__exports

    @property
    def interface(self):
        return self.__interface

    @property
    def platform_target(self):
        return scaffold.variant.get_variant('platform_target')

    @property
    def arch(self):
      return scaffold.variant.get_variant('arch')
    def _init_defaults(self):

        pydir_name = 'python{}.{}'.format(sys.version_info.major, sys.version_info.minor)
        py_reldir = 'lib/{}/site-packages'.format(pydir_name)
        platform_target = scaffold.variant.get_variant('platform_target')

        self.__interface.update({
            'inst_top_dir': 'inst/{}'.format(platform_target),
            'pydir_name': pydir_name,
            'py_reldir': py_reldir
        })


    def inherit(self, benv):

        self.__exports = benv.exports

        i_keys = [
            'root_dir',
            'sset_name',
            'sset_rname',
            'sset_dir',
            'sset_inst_dir',
            'product_name',
            'product_dir',
            'product_config'
        ]

        for i_key in i_keys:
            if benv.interface.get(i_key) is not None:
                self.__interface[i_key] = benv.interface[i_key]




    def __setattr__(self, key, value):
        if key.startswith('_'):
            return object.__setattr__(self, key, value)

        self.__interface[key] = value

    def __getattr__(self, key):
        if key.startswith('_'):
            return object.__getattr__(self, key)

        if key in self.__interface:
            return self.__interface[key]

        else:
            raise AttributeError(key)

    def register_builder(self, builder_cls, *args):
        builder_obj = builder_cls(self, args)
        self.__builders.append(builder_obj)

        return builder_obj

    def gen_rules(self):

        n = ''
        for builder in self.__builders:
            n += builder.gen_rules()
            n += '\n'

        return n

    def gen_build(self):
        n = ''
        for builder in self.__builders:
            n += builder.gen_build()
            n += '\n'

        return n
