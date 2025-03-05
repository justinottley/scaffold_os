#
# Copyright 2014-2024 Justin Ottley
#
# Licensed under the terms set forth in the LICENSE.txt file
#

import re

from . import PathStyle
from .. import util as pathutil

class UNCPathStyle(PathStyle):

    UNC_RE = re.compile(r'^(//\w+/\w+)/\w+|(\\\\\w+\\\w+)\\\w+|(\\\\[\w\-]+\\\w+)')

    def detect(self, path_in, translation_config):

        result = re.match(self.UNC_RE, path_in)

        if result:

            groups = result.groups()
            assert(groups[0] or groups[1] or groups[2])

            self.LOG.debug('OK: {}'.format(path_in))

            if groups[0]:
                anchor_parts = pathutil.split_path(groups[0])

            elif groups[1]:
                anchor_parts = pathutil.split_path(groups[1])

            elif groups[2]:
                anchor_parts = pathutil.split_path(groups[2])

            path_parts = pathutil.split_path(path_in)

            
            return self._build_path_info(path_parts, anchor_parts, translation_config)


    def format(self, path_info, translation_map, sep='\\', **kwargs):

        anchor_list = self._get_anchor_list(path_info, translation_map)
        if anchor_list:
            leading_seps = '{sep}{sep}'.format(sep=sep)
            result = '{val}{sep}{path_list}'.format(
                val=sep.join(anchor_list),
                sep=sep,
                path_list=sep.join(path_info.path_list)
            )

            # HACK: if the formatted path is actually a drive letter, dont
            # attempt to put the leading seps
            #
            if result[1] != ':' and not result.startswith(leading_seps):
                result = '{}{}'.format(leading_seps, result)

            return result
