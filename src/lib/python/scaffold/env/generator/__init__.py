#
# Copyright 2014-2024 Justin Ottley
#
# Licensed under the terms set forth in the LICENSE.txt file
#

import os
import sys
import logging

import scaffold.variant


class EnvGenerator(object):

    def __init__(self, cntrl):

        self.LOG = logging.getLogger('{}.{}'.format(self.__class__.__module__, self.__class__.__name__))

        self.cntrl = cntrl
        self.messages = []


    @classmethod
    def create(cls, cntrl):

        env_generator_cls = None

        if scaffold.variant.get_variant('opsys') == 'Windows':

            from .windows import WindowsEnvGenerator
            env_generator_cls = WindowsEnvGenerator

        else:
            from .posix import PosixEnvGenerator
            env_generator_cls = PosixEnvGenerator


        assert(env_generator_cls)

        env_generator_obj = env_generator_cls(cntrl)

        return env_generator_obj



    def compile_env(self):
        '''
        compile a dictionary of the final output environment
        '''

        # add compiled env
        result = {}
        for env_entry in self.cntrl.env:

            env_value = ''

            # a path-like variable, consider as a colon delimited list
            # XXX: this may be a bit naive of a generalization
            if 'PATH' in env_entry:
                env_value = os.pathsep.join(self.cntrl.env[env_entry])

            else:
                env_value = self.cntrl.env[env_entry]

            result[env_entry] = env_value


        return result


    def update_env(self):
        '''
        Update the environment in this process with the output of the
        runtime environment configuration
        
        NOTE: DEPRECATE THIS
        '''
        
        self.LOG.warning('DeprecationWarning: Danger - do not call update_env() -'\
            'major side effects in current process')


        env = self.compile_env()
        
        for entry in reversed(env['PYTHONPATH'].split(os.pathsep)):
            
            if not entry:
                continue
                
            self.LOG.debug('Adding to sys.path: {e}'.format(e=entry))
            sys.path.insert(0, entry)
        
        os.environ.update(env)


    def generate_env_file(self, messages=None):
        '''
        Generate a platform specific representation of an environment that
        can be sourced on that platform to setup the environment
        '''
        
        raise NotImplementedError
        