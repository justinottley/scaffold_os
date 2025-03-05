#
# Copyright 2014-2024 Justin Ottley
#
# Licensed under the terms set forth in the LICENSE.txt file
#

import os
import pprint
import logging
import collections

from .exception import PathFormatError
from . import translation

LOG = logging.getLogger(__name__)

PathInfo = collections.namedtuple('PathInfo',
    ['style_name', 'path_list', 'anchor_list', 'mapping_name', 'extra'])


class Path(object):

    _style_types = collections.OrderedDict()

    # A list of callables that implement string substitution formatting for {key}
    # by calling format(key=value)
    subst_handlers = []

    def __init__(self, path_in, default_style=None, translation_map=None, **kwargs):
        '''
        default_style: dictionary containing info on default style, if different
        from current platform
        e.g., {'name': 'UNC'}

        translation_map: list of dicts, translation map
        '''
        self.styles = collections.OrderedDict()

        # Instantiate styles. A bit heavy, but because of ability to
        # change behavior like translation_map per Path, we need
        # per Path-object Style objects.
        # Can this be optimized?
        #
        for style_cls in self._style_types.values():
            style_obj = style_cls(
                translation_map=translation_map,
                **kwargs
            )
            self.styles[style_obj.name] = style_obj


        self.__path_in = None
        self.__path_info = None

        self.default_style = default_style or self._detect_default_style()

        # Support for different input types
        #
        if isinstance(path_in, Path):
            self._copy(path_in)

        elif isinstance(path_in, PathInfo):
            self.__path_info = PathInfo(**path_in)

        else:
            self.__path_in = path_in
            self._detect()

    def __str__(self):
        '''
        Return a formatted path appropriate for the current platform
        '''

        if not self.__path_info:

            LOG.warning('path detection failed, returning original input: "{}"'.format(self.__path_in))
            return self.__path_in

        style_name = self.default_style['name']
        style_kwargs = self.default_style.get('kwargs', {})

        return self.format(style_name, **style_kwargs)


    @classmethod
    def register_style(cls, style_cls):
        cls._style_types[style_cls.__name__] = style_cls


    @staticmethod
    def set_translation_map(translation_map):

        # NOTE: Late import
        from .style import PathStyle
        PathStyle._TRANSLATION_MAP = translation_map


    @property
    def path_info(self):
        return self.__path_info


    @classmethod
    def get_default_style(self):
        '''
        TODO FIXME: move to PathStyle?
        '''

        if os.name == 'nt':
            return 'DriveLetter'

        else:
            return 'Posix'


    def _copy(self, path_in):
        raise NotImplementedError('_copy() on Path not implemented for {}'.format(path_in))


    def _detect(self):

        for tmap_info in translation.TRANSLATION_CONFIG:

            if not tmap_info.enabled:

                LOG.log(9, 'skipping translation config: "{}"'.format(tmap_info.name))
                continue

            for style_handler in self.styles.values():

                path_info = style_handler.detect(self.__path_in, tmap_info)
                if path_info:
                    self.__path_info = path_info

                    LOG.log(9, path_info)

                    break

            if self.__path_info != None:
                break

    def _detect_default_style(self):
        # TODO FIXME: DEPRECATE
        default_style = self.get_default_style()
        return {'name': default_style}


    def format(self, style_name=None, **kwargs):

        if not style_name:
            style_name = self.get_default_style()

        if not self.__path_info:
            msg = 'Cannot be formatted - path detection failed! call str() instead - (original input: {})'.format(
                self.__path_in)
            raise PathFormatError(msg)

        result = None

        translation_config = translation.TRANSLATION_CONFIG
        if kwargs.get('translation_config'):
            translation_config = kwargs['translation_config']


        if kwargs.get('translation_map'):
            translation_config = [translation.get_config(kwargs['translation_map'])]
            kwargs.pop('translation_map')

        if style_name in self.styles:

            for tmap_info in translation_config:
                
                if not tmap_info.enabled:
                    continue
                
                LOG.log(9, 'attempting translation config: "{}"'.format(tmap_info.name))

                validate_func = tmap_info.validate_func
                translation_map =  tmap_info.translation_map
                style_handler = self.styles[style_name]

                formatted_path = style_handler.format(
                    self.__path_info,
                    tmap_info.translation_map,
                    **kwargs
                )

                if not formatted_path:
                    continue

                for subst_handler in self.subst_handlers:
                    formatted_path = subst_handler.format(formatted_path)
                
                validate_result = validate_func(
                    formatted_path,
                    self.__path_info,
                    style_handler,
                    translation_map
                )

                if validate_result or kwargs.get('force_validate'):
                    result = formatted_path
                    break


        if result is None:
            raise PathFormatError('Style not available: "{}" - {}'.format(style_name, self.__path_info))


        return result


def _init():

    LOG.log(9, '')

    translation._init_translation_config()
    
    from .style.unc import UNCPathStyle
    from .style.drive_letter import DriveLetterPathStyle
    from .style.posix import PosixPathStyle, RFSPathStyle
    from .style.uri import URIPathStyle

    for style_cls in [
        UNCPathStyle, DriveLetterPathStyle, PosixPathStyle, URIPathStyle, RFSPathStyle
    ]:
        Path.register_style(style_cls)


_init()
del _init