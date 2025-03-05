#
# Copyright 2014-2024 Justin Ottley
#
# Licensed under the terms set forth in the LICENSE.txt file
#

import os

import scaffold.variant
from scaffold.buildsys import buildlib

from .. import util as buildsys_util

_RULES_DONE = False

def configure_env(benv):

    reldir = benv.node.reldir

    header_list = []
    cpp_list = []
    if 'cpp_classes' in benv.interface:
        for class_entry in benv.cpp_classes.split():
            class_entry = class_entry.strip()

            header_relpath = os.path.join(reldir, '{}.h'.format(class_entry))
            cpp_relpath = os.path.join(reldir, '{}.cpp'.format(class_entry))

            header_list.append(header_relpath)
            cpp_list.append(cpp_relpath)


    benv.headers = header_list
    benv.cpps = cpp_list

    benv.shlib_inst_dir = os.path.join(benv.sset_inst_dir, 'lib')

    benv.sset_gen_dir = os.path.join(benv.sset_inst_dir, '_gen')
    benv.sset_gen_lib_dir = os.path.join(benv.sset_gen_dir, 'lib', benv.lib_name)

    # NOTE: Disable product specific gen include and lib dirs, write everything
    #       to sset directly since product lib names must be unique anyway across
    #       the sset
    # benv.product_inst_dir = os.path.join('{}/{}/_products/{}'.format(
    #     benv.inst_top_dir, benv.sset_name, benv.product_name))

    # benv.product_include_dir = os.path.join(benv.product_inst_dir, 'include')
    # benv.product_gen_dir = os.path.join(benv.product_inst_dir, '_gen')
    # benv.product_gen_lib_dir = os.path.join(benv.product_gen_dir, 'lib', benv.lib_name)


def _configure_builders(benv):


    bl_opsys = buildlib.get_lib('OpSys')
    bl_opsys.init(benv)

    bl_sset = buildlib.get_lib('SSet')
    
    thirdparty_info = buildsys_util.get_required_thirdparty_info(benv.required_thirdparty_libs)

    blib_map = {}
    for tp_entry in thirdparty_info:

        tp_name = tp_entry[0]

        bl = buildlib.get_lib(tp_name)
        if bl is None:
            raise Exception('Platform not supported for {}'.format(tp_name))
        bl.init(benv)

        blib_map[tp_name] = bl

    
    # init software set after 3rd party deps so libs get provided
    # to linker in correct order
    bl_sset.init(benv)

    bl_reqs = []
    b_ch = benv.register_builder(bl_opsys.builder('CopyHeaders'))
    bl_reqs.append(b_ch)

    if 'Qt' in blib_map:

        bl_qt = blib_map['Qt']
        b_moc = benv.register_builder(bl_qt.builder('Moc'))
        
        blib_map['Moc'] = b_moc
        bl_reqs.append(b_moc)

        b_rcc = benv.register_builder(bl_qt.builder('RCC'))
        bl_reqs.append(b_rcc)


    if 'PyBind11' in blib_map and 'Qt' in blib_map:

        bl_pb11 = blib_map['PyBind11']
        b_moc = blib_map['Moc']

        b_pb11 = benv.register_builder(bl_pb11.builder('PB11Gen'), b_moc)
        bl_reqs.append(b_pb11)

    b_libs = benv.register_builder(bl_sset.builder('DependentLibs'))
    bl_reqs.append(b_libs)

    b_o = benv.register_builder(bl_opsys.builder('Object'), *bl_reqs)
    
    return b_o

def configure_builders(benv):
    b_o = _configure_builders(benv)

    bl_opsys = buildlib.get_lib('OpSys')
    b_sh = benv.register_builder(bl_opsys.builder('SharedLib'), b_o)

    # TODO FIXME HACK
    global _RULES_DONE
    if not _RULES_DONE:

        # TURN THIS ON TO WRITE RULES
        r = benv.gen_rules()
        r += '\n'
        
        rules_path = 'build/gen/{}/rules.ninja'.format(
            scaffold.variant.get_variant('platform_target'))

        with open(rules_path, 'w') as wfh:
            wfh.write(r)

        _RULES_DONE = True



    return b_sh
    
    

