#
# Copyright 2014-2024 Justin Ottley
#
# Licensed under the terms set forth in the LICENSE.txt file
#

from . import PathStyle

from .. import util as pathutil


class PosixPathStyle(PathStyle):

    def detect(self, path_in, translation_config):

        if '\\' not in path_in and \
        path_in[0] == '/' and \
        (len(path_in) > 1 and path_in[1] != '/'):

            self.LOG.debug('OK: {}'.format(path_in))

            path_parts = pathutil.split_path(path_in)
            anchor_parts = []

            return self._build_path_info(
                path_parts,
                anchor_parts,
                translation_config
            )


    def format(self, path_info, translation_map, **kwargs):

        result = None
        anchor_list = self._get_anchor_list(
            path_info, translation_map)

        anchor = ''
        if anchor_list:
            anchor = '/'.join(anchor_list)

            result = '{}/{}'.format(
                anchor, '/'.join(path_info.path_list)
            )
        if not result.startswith('/'):
            result = '/{}'.format(result)


        return result


class RFSPathStyle(PosixPathStyle):
    pass

