#
# Copyright 2014-2024 Justin Ottley
#
# Licensed under the terms set forth in the LICENSE.txt file
#

import os
import logging
from itertools import zip_longest

from .. import PathInfo
from ..exception import PathResolutionError

class PathStyle(object):

    def __init__(self, *args, **kwargs):

        self.LOG = logging.getLogger('{}.{}'.format(
            self.__class__.__module__, self.name))

    @property
    def name(self):
        return self.__class__.__name__.replace('PathStyle', '')

    def _build_path_info(self, path_parts, anchor_parts, translation_config, extra=None):

        if extra is None:
            extra = {}

        mapping_name = None
        path_result = []

        for mapping_info in translation_config.translation_map:

            self.LOG.log(9, '{} - attempting {}'.format(self.name, mapping_info))

            if self.name not in mapping_info['mapping']:
                continue
            
            if 'enabled' in mapping_info and not mapping_info['enabled']:
                continue

            config_path_parts = mapping_info['mapping'][self.name]

            # If the incoming config's path list (anchor) is longer than the incoming path,
            # we already know the path we're attempting is not a match, so move on to the next
            # mapping if we find that case
            #
            if len(config_path_parts) > len(path_parts):
                continue

            for (mapping_item, path_item) in zip(config_path_parts, path_parts):

                if mapping_item != path_item:

                    self.LOG.log(9, 'mismatch: mapping_item: {} path_item: {}'.format(
                        mapping_item, path_item
                    ))

                    break

            else:

                mapping_name = mapping_info['name']
                anchor_parts = list(map(str, mapping_info['mapping'][self.name]))
                extra['translation_config'] = translation_config.name

                break

        # remove the anchor from the path
        #
        for (path_item, anchor_item) in zip_longest(path_parts, anchor_parts):

            if anchor_item and anchor_item == path_item:
                continue

            path_result.append(path_item)

        if mapping_name:
            return PathInfo(self.name, path_result, anchor_parts, mapping_name, extra)


    def _get_anchor_list(self, path_info, translation_map):

        anchor_list = None

        if path_info.mapping_name:
            for mapping_info in translation_map:
                
                if 'enabled' in mapping_info and not mapping_info['enabled']:
                    continue

                if mapping_info['name'] == path_info.mapping_name:

                    anchor_list = []
                    raw_anchor_list = mapping_info['mapping'].get(self.name)
                    for raw_entry in raw_anchor_list:

                        if hasattr(raw_entry, 'value'):
                            anchor_value = raw_entry.value(path_info)
                        else:
                            anchor_value = str(raw_entry)

                        # resolve env. variables
                        if anchor_value.startswith('$'):
                            ranchor_value = os.getenv(anchor_value[1:])
                            if ranchor_value is None:
                                raise PathResolutionError('env. variable not found: {}'.format(anchor_value))

                            anchor_value = ranchor_value

                        anchor_list.append(anchor_value)

                    # except Exception as e:
                    #     self.LOG.log(9, 'error getting anchor list for {}, style: {} - {}: {}'.format(
                    #         mapping_info['name'],
                    #         self.name,
                    #         e.__class__.__name__,
                    #         e
                    #     ))


                    # if this mapping does not support this style, then the
                    # anchor list should be empty. Break in this case as well
                    break

        return anchor_list


    def detect(self, path_in, translation_map):
        pass

    def format(self, path_data, translation_map, *args, **kwargs):
        pass


