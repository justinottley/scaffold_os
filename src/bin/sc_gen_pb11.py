#!/usr/bin/env python3
#
# Copyright 2014-2024 Justin Ottley
#
# Licensed under the terms set forth in the LICENSE.txt file
#

import os
import sys
import base64
import argparse



from scaffold.buildsys.buildlib.PyBind11 import generator as pb11_generator


def main():


    parser = argparse.ArgumentParser('')
    parser.add_argument('--mode', dest='mode', required=True) # static (embedded) or dynamic (not embedded)
    parser.add_argument('--sset_rname', dest='sset_rname', required=True)
    parser.add_argument('--lib_name', dest='lib_name', required=True)
    # parser.add_argument('--o_header', help='header output path', required=True)
    # parser.add_argument('--o_cpp', help='cpp output path', required=True)
    parser.add_argument('--outputs', nargs=4, help='header, sigslot, and cpp outputs')
    parser.add_argument('--src_headers', nargs='*', required=True)
    parser.add_argument('--src_jsons', nargs='*', required=True)

    parser.add_argument('--pb_info', required=True)

    args = parser.parse_args()

    o_header, o_ssc_header, o_ssc_moc_cpp, o_cpp = args.outputs

    pb11_generator.generate_pybind11_module(
        args.mode,
        args.sset_rname,
        args.lib_name,
        args.pb_info,
        o_header,
        o_ssc_header,
        o_ssc_moc_cpp,
        o_cpp,
        args.src_headers,
        args.src_jsons
    )


if __name__ == '__main__':
    main()