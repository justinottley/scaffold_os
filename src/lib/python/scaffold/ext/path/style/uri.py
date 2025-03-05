#
# Copyright 2014-2024 Justin Ottley
#
# Licensed under the terms set forth in the LICENSE.txt file
#

import traceback

from . import PathStyle

class URIPathStyle(PathStyle):

    SENTINEL = '://'

    def detect(self, path_in, translation_config):
        
        uri_parts = path_in.split(self.SENTINEL)

        if len(uri_parts) == 2:

            self.LOG.log(9, 'OK: {}'.format(path_in))

            mapping_parts, uri_rest = uri_parts
            mapping_info = mapping_parts.split('@')
            mapping = mapping_info[0]

            self.LOG.log(9, '{} {}'.format(mapping_parts, mapping_info))

            extra = None


            if len(mapping_info) > 1:
                extra = {}
                try:
                    for kv_entry in mapping_info[1].split('&'):
                        key, value = kv_entry.split('=')
                        extra[key] = value

                except Exception as e:
                    self.LOG.warning('could not parse URI metadata from {} - {}'.format(mapping_parts, e))
                    self.LOG.log(9, traceback.format_exc())


            path_parts = [mapping] + uri_rest.split('/')
            anchor_parts = [mapping]

            return self._build_path_info(path_parts, anchor_parts, translation_config, extra=extra)


    def format(self, path_info, translation_map, **kwargs):

        ns_part = path_info.mapping_name
        metadata = ''

        if 'hostname' in path_info.extra:
            
            # TODO FIXME: serialize kv metadata
            metadata = '@hostname={}'.format(path_info.extra['hostname'])


        result = '{}{}://{}'.format(
            ns_part,
            metadata,
            '/'.join(path_info.path_list)
        )

        return result

