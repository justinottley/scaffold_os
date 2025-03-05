#!/usr/bin/env python3
#
# Copyright 2014-2024 Justin Ottley
#
# Licensed under the terms set forth in the LICENSE.txt file
#

import os
import sys


def main():

    cmd = 'rlp_py_gui.bin scaffold.ext.gui {}'.format(sys.argv[1])
    print(cmd)
    os.system(cmd)


if __name__ == '__main__':
    main()