#!/usr/bin/env python3

import os
import sys
import argparse

def main():

    parser = argparse.ArgumentParser('')
    parser.add_argument('-o', dest='output')
    parser.add_argument('--emdir')
    parser.add_argument('src_files', nargs='*')
    args = parser.parse_args()

    emdir_path = os.path.join(args.emdir, 'emar')
    emranlib_path = os.path.join(args.emdir, 'emranlib')


    sh_output = sys.argv[1]
    input_list = sys.argv[2:]

    emar_cmd = '{} rc {} {}'.format(
        emdir_path, args.output, ' '.join(args.src_files))

    emranlib_cmd = '{} {}'.format(emranlib_path, args.output)

    print(emar_cmd)
    os.system(emar_cmd)

    print(emranlib_cmd)
    os.system(emranlib_cmd)


if __name__ == '__main__':
    main()