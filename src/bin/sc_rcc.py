#!/usr/bin/env python3
#
# Copyright 2014-2024 Justin Ottley
#
# Licensed under the terms set forth in the LICENSE.txt file
#

import os
import sys
import tempfile
import argparse

import scaffold.variant

from scaffold.buildsys.benv import BuildEnvironment

def gen_qrc(root_dir, base_dir, src_file_list):

    qrc_text = '''
<!DOCTYPE RCC><RCC version="1.0">
<qresource>
'''

    r_path_prefix = '' # env['resource_path_prefix']

    for source_entry in src_file_list:
        source_entry = source_entry.strip()
        source_path = os.path.join(root_dir, base_dir, source_entry)
        # source_alias = source_path.replace(r_path_prefix, '').replace('\\', '/')
        qrc_entry = '    <file alias="{}">{}</file>'.format(
            source_entry,
            source_path
        )
        qrc_text += '{}\n'.format(qrc_entry)

    qrc_text += '''
</qresource>
</RCC>
'''
    return qrc_text

def main():


    parser = argparse.ArgumentParser('')
    parser.add_argument('--platform_target')
    parser.add_argument('--rcc')
    parser.add_argument('--root_dir')
    parser.add_argument('--output')
    parser.add_argument('--input')

    args = parser.parse_args()

    platform_target = args.platform_target
    if not platform_target:
        platform_target = scaffold.variant.get_variant('opsys')

    scaffold.variant.register_variant('platform_target', platform_target)

    root_dir = args.root_dir
    ss_script = args.input
    output_cpp = args.output
    output_qrc = output_cpp.replace('.cpp', '.qrc')


    if not os.path.isfile(ss_script):
        print('File not found: {}'.format(ss_script))
        sys.exit(1)


    qrc_text = ''
    with open(ss_script) as fh:
        contents = fh.read()
        benv = BuildEnvironment()
        exec(contents, {'benv': benv})

        static_files = benv.static_files.split()
        base_dir = os.path.dirname(ss_script)

        qrc_text = gen_qrc(root_dir, base_dir, static_files)


    if not qrc_text:
        print('No output QRC!')
        sys.exit(2)

    with open(output_qrc, 'w') as wfh:
        wfh.write(qrc_text)

    print('Wrote {}'.format(output_qrc))

    init_name = os.path.basename(output_cpp).replace('.cpp', '')

    rcc_cmd = '{} --no-zstd --name {} -o {} {}'.format(
        args.rcc, init_name, output_cpp, output_qrc
    )
    print(rcc_cmd)
    os.system(rcc_cmd)





if __name__ == '__main__':
    main()