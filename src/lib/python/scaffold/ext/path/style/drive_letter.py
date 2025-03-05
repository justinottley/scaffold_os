#
# Copyright 2014-2024 Justin Ottley
#
# Licensed under the terms set forth in the LICENSE.txt file
#

import re

from . import PathStyle

from .. import util as pathutil

class DriveLetterPathStyle(PathStyle):

    DRIVE_LETTER_RE = re.compile('^[a-zA-Z]:')

    def detect(self, path_in, translation_config):

        result = re.match(self.DRIVE_LETTER_RE, path_in)

        if result:

            value = result.group()
            value = value.capitalize()

            path_parts = pathutil.split_path(path_in)

            # sanity / support for multiple casing for drive letters....
            #
            if re.match(self.DRIVE_LETTER_RE, path_parts[0]):
                path_parts[0] = path_parts[0].capitalize()

            anchor_parts = [value]

            return self._build_path_info(path_parts, anchor_parts, translation_config)


    def format(self, path_info, translation_map, sep='\\', **kwargs):

        anchor_list = self._get_anchor_list(path_info, translation_map)
        if anchor_list:

            anchor_root = anchor_list[0]
            anchor_rest = ''
            if len(anchor_list) > 1:
                anchor_rest = '{}{}'.format(
                    sep.join(anchor_list[1:]),
                    sep
                )

            result = '{}{}{}{}'.format(
                anchor_root,
                sep,
                anchor_rest,
                sep.join(path_info.path_list)
            )
            result = result.replace('\\\\', '\\')

            return result