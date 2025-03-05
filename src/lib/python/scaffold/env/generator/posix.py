#
# Copyright 2014-2024 Justin Ottley
#
# Licensed under the terms set forth in the LICENSE.txt file
#

import os
import sys
import tempfile

from scaffold.env.generator import EnvGenerator

class PosixEnvGenerator(EnvGenerator):
    
    SC_TEMP_DIR = os.path.join(tempfile.gettempdir(), os.getenv('USER', os.getenv('USERNAME')), 'vc', 'env')
    
    def _generate_empty_env(self):
        
        result = ''
        for key in os.environ.keys():
            
            # workaround for weird BASH_FUNC_module() variable
            if '()' in key:
                continue
                
            result += 'unset {key}\n'.format(key=key)
            
        return result
        
        
    def _generate_env(self, environ, result, messages):
        '''
        A standalone routine to generate an environment for the target
        platform, using an input dictionary environment
        '''
        
        # function to get current git branch - 
        # From https://coderwall.com/p/fasnya/add-git-branch-name-to-bash-prompt
        #
        result += "parse_git_branch() {\ngit branch 2> /dev/null | sed -e '/^[^*]/d' -e 's/* \\(.*\\)/ (\\1)/'\n}\n"
        
        # python alias
        #
        result += "alias python=python{}.{}\n".format(sys.version_info.major, sys.version_info.minor)

        for logrecord in messages:
            
            if logrecord.levelname == 'INFO':
                result += "echo '{msg}'\n".format(msg=logrecord.msg)
                
            else:
                echo_msg = "echo {name} [ {levelname} ] : '{msg}'\n"
                echo_msg = echo_msg.format(name=logrecord.name,
                                           levelname=logrecord.levelname,
                                           msg=logrecord.msg)
                
                result += echo_msg
        
        
        source_list = []
        for env_entry, env_value in environ.items():
            
            # print '{} - {}'.format(env_entry, env_value)

            if env_entry.startswith('__source'):
                source_list.append(env_value)
                

            else:
                # we're assuming bash as the shell
                result += "export {}='{}'\n".format(
                    env_entry, env_value)
            
        
        for source_entry in source_list:
            result += 'source {}\n'.format(source_entry)

        return result
        
        
    def _format_prompt(self):

        build_version_tag = self.cntrl.config['__bootstrap__']['build_version']
        
        # if there is a path override in any of the top-level packages,
        # add a "dev" tag to the prompt
        # NOTE: all builds now have an "override path", i.e., a full path
        # in the generated vc config, so the +dev is now applied via
        # prompt.tag_custom in SConscript.local for dev builds
        #
        '''
        for sft_set_name in self.cntrl.software_sets:
            if self.cntrl.software_sets[sft_set_name].has_override_path:
                build_version_tag += '+dev'
                break
        '''
        
        if 'prompt.tag_custom' in self.cntrl.config['__bootstrap__']:
           build_version_tag += self.cntrl.config['__bootstrap__']['prompt.tag_custom']
        
        # set the prompt with the build version
        # reference: https://wiki.archlinux.org/index.php/Color_Bash_Prompt
        
        
        prompt_cmd = ''
        
        if 'prompt.custom' in self.cntrl.config['__bootstrap__']:
            prompt_cmd += self.cntrl.config['__bootstrap__']['prompt.custom']
            
        else:
            
            if 'prompt.user' in self.cntrl.config['__bootstrap__']:
                prompt_cmd += "$(whoami) "
            
            if 'prompt.hostname' in self.cntrl.config['__bootstrap__']:
                prompt_cmd += "$(hostname) "
                
            if 'prompt.userhost' in self.cntrl.config['__bootstrap__']:
                prompt_cmd += "$(whoami)@$(hostname) "
                
            if 'prompt.currdir' in self.cntrl.config['__bootstrap__']:
                prompt_cmd += "\W "
                
            if 'prompt.currpath' in self.cntrl.config['__bootstrap__']:
                prompt_cmd += "$(pwd)"
            
            if 'prompt.git.branch' in self.cntrl.config['__bootstrap__']:
                prompt_cmd += '\[\033[33m\]$(parse_git_branch)\[\033[00m\]'
                
                
            # add some decoration and newline if configured
            #
            if prompt_cmd:
                prompt_cmd = '[ {} ]'.format(prompt_cmd)
                
            if 'prompt.newline' in self.cntrl.config['__bootstrap__']:
                prompt_cmd = '{}\n'.format(prompt_cmd)
                
        # prompt_cmd += '''\[\e[1;34m\][ {build_version_tag} ]'''
        # prompt_cmd += ''' \[\e[0;37m\]\$\[\e[0m\]'''
        prompt_cmd += r'''\[\033[01;32m\]\u@\h\[\033[00m\]:\[\033[01;34m\]\w\[\033[00m\]\n\[\e[1;34m\][ {build_version_tag} ]\[\e[0;37m\]\[\e[0m\] \$'''
        prompt_cmd = prompt_cmd.format(build_version_tag=build_version_tag)
        
        return prompt_cmd
        
        
    def generate_env(self, messages=None):
        
        if messages is None:
            messages = []
        
        
        # build bash script
        
        file_contents = '#!/bin/bash\n#\n'
        file_contents += '# Automatically generated by scaffold.vc\n#\n'
        
        file_contents += self._generate_env(
            self.compile_env(),
            file_contents,
            messages)
        
        
        prompt_cmd = self._format_prompt()
        
        set_prompt_cmd = '''PS1='{} ' \n'''.format(prompt_cmd)
        
        # set_prompt_cmd = set_prompt_cmd.format(
            
        file_contents += set_prompt_cmd
        
        
        return file_contents
        
        
    def generate_env_file(self, messages=None, extra_commands=None):
        
        tempfd, temp_filename = tempfile.mkstemp(dir=self.SC_TEMP_DIR)

        file_contents = self.generate_env(messages)
        
        if extra_commands:
            file_contents += extra_commands
            file_contents += '\n'
            
        
        if not os.path.isdir(self.SC_TEMP_DIR):
            os.makedirs(self.SC_TEMP_DIR)
            
        
        os.write(tempfd, bytes(file_contents, "utf8"))
        os.close(tempfd)
        os.chmod(temp_filename, 0o777)
        
        
        return temp_filename
        
    
    