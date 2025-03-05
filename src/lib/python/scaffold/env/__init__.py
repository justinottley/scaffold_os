#
# Copyright 2014-2024 Justin Ottley
#
# Licensed under the terms set forth in the LICENSE.txt file
#

import os
import logging

LOG = logging.getLogger(__name__)

import scaffold.util

def _get_root_config():
    return {'export_env': {}}


def load_config(config_path=None, config_loader=None, config_init_kwargs=None):

    config_init_kwargs = config_init_kwargs or {}

    if config_path is None:
        inst_dir = scaffold.util.get_inst_dir()
        config_path = os.path.join(inst_dir, 'etc', 'sc_config.json')


    if config_loader is None:
        if os.getenv('SC_CONFIG_LOADER'):

            # This is used for example if we want to initialize an
            # EnvController (like for an application executble wrapper script)
            # inside an already initialized environment. In this case,
            # we want to bring up the already setup config and loader

            config_loader = os.environ['SC_CONFIG_LOADER']
            LOG.debug('Using config loader from environment: {cl}'.format(
                cl=config_loader))

        else:

            # "compiled in" default
            #
            config_loader = 'Build'


    from . import loader

    loader_cls_name = '{}ConfigLoader'.format(config_loader)
    if not hasattr(loader, loader_cls_name):
        raise Exception('Invalid loader name: {}'.format(config_loader))


    loader_cls = getattr(loader, loader_cls_name)
    LOG.debug('Got loader: {}'.format(loader_cls))

    loader_obj = loader_cls(_get_root_config(), **config_init_kwargs)
    LOG.debug('Created loader: {}'.format(loader_obj))

    return loader_obj.load_config(config_path)

