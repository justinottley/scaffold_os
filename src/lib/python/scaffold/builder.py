#
# Copyright 2014-2024 Justin Ottley
#
# Licensed under the terms set forth in the LICENSE.txt file
#

import os
import json
import logging

from scaffold import gitutil

class Builder(object):

    def __init__(self, git_url,
                       git_branch='master',
                       flavour='master',
                       base_dir=None
                ):

        self.LOG = logging.getLogger('{}.{}'.format(self.__class__.__module__, self.__class__.__name__))

        self.git_url = git_url
        self.git_branch = git_branch
        self.build_flavour = flavour

        self.base_dir = base_dir or os.getcwd()
        self.repo_dir = os.path.join(self.base_dir, gitutil.get_repo_dirname(self.git_url))
        self.src_dir = os.path.join(self.repo_dir, 'src')
        self.build_config_path = os.path.join(self.repo_dir, 'build', 'flavour', self.build_flavour, 'sc_config.json')


    def clone_superproject(self):

        self.LOG.info('Cloning superproject to {}'.format(self.base_dir))
        if not os.path.isdir(self.base_dir):

            self.LOG.info('Creating {}'.format(self.base_dir))

            os.makedirs(self.base_dir)

        self.LOG.debug('chdir: {}'.format(self.base_dir))
        os.chdir(self.base_dir)

        self.LOG.info('URL: {} Branch: Flavour: {}'.format(
            self.git_url, self.git_branch, self.build_flavour
        ))

        git_clone_cmd = 'git clone {}'.format(self.git_url)
        self.LOG.debug(git_clone_cmd)

        result = os.system(git_clone_cmd)

        os.chdir(self.repo_dir)

        git_checkout_cmd = 'git checkout {}'.format(self.git_branch)
        self.LOG.debug(git_checkout_cmd)

        result = os.system(git_checkout_cmd)

        build_config = {}

        print(self.build_config_path)
        with open(self.build_config_path) as fh:
            build_config = json.load(fh)


        for bkey, bval in build_config.items():
            if bkey == '__bootstrap__':
                continue
            
            if bval['sftset_type'] != 'int':
                self.LOG.info('Skipping non-int Software Set: {}'.format(bkey))
                continue


            self.LOG.info('')
            self.LOG.info(bkey)

            # sftset_relpath =  # or bkey
            sftset_dir = os.path.join(self.repo_dir, bval['sftset_src_relpath'])
            if not os.path.isdir(sftset_dir):
                self.LOG.debug('Creating: {}'.format(sftset_dir))
                os.makedirs(sftset_dir)

    
            for project_name, project_config in bval['projects'].items():
                
                project_git_url = project_config['git_url']
                project_git_branch = project_config['git_branch']
                project_src_relpath = project_config['project_src_relpath']

                project_dirname = project_config.get('project_dirname')

                # skip any projects whose git repo is the superproject repo
                if project_git_url == self.git_url:
                    self.LOG.debug('Skipping: {}'.format(project_name))
                    continue

                if project_dirname:
                    project_src_relpath = os.path.join(project_src_relpath, project_dirname)

                self.LOG.debug('chdir: {}'.format(sftset_dir))
                os.chdir(sftset_dir)

                git_clone_cmd = 'git clone -b {} {} {}'.format(
                    project_git_branch, project_git_url, project_src_relpath
                )

                self.LOG.debug(git_clone_cmd)
                os.system(git_clone_cmd)


    def build_superproject(self):

        gen_cmd = 'scgen --config'

        self.LOG.debug('chdir: {}'.format(self.repo_dir))
        os.chdir(self.repo_dir)

        self.LOG.info(gen_cmd)
        os.system(gen_cmd)

        build_cmd = 'scb'
        self.LOG.info(build_cmd)
        os.system(build_cmd)