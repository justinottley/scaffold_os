#
# Copyright 2014-2024 Justin Ottley
#
# Licensed under the terms set forth in the LICENSE.txt file
#

import os
import sys
import json
import pprint
import shutil
import tempfile
import subprocess

import scaffold.variant
from scaffold.env.sset_mgr import SoftwareSetManager
from scaffold.ext.path import Path


SITE_NAME = 'rlp_test'
TB_ROOT = '/home/justinottley/dev/revlens_root/thirdbase'
PLATFORM = scaffold.variant.get_platform()

# Exit Codes
ERR_FS_NOT_AVAILABLE = 1
ERR_INVALID_PROJECT = 2
ERR_SSET_NOT_FOUND = 3

edbc = None

PROJECT_MAP = {}

ZCMD = '7zz'
if os.name == 'nt':
    ZCMD = '7z.exe'

CPCMD = 'cp'
if os.name == 'nt':
    CPCMD = 'copy'

def _to_ver_num(sset_zip_name, sset_name):
    name_prefix = 'sset_{}_'.format(sset_name)
    return int(sset_zip_name.replace(name_prefix, '').replace('.7z', ''))


def _get_next_ver(sset_inst_root, sset_name):

    ver_list = os.listdir(sset_inst_root)
    if not ver_list:
        return str(1).zfill(4)

    max_ver = 0
    for entry in ver_list:
        ver_num = _to_ver_num(entry, sset_name)
        if ver_num > max_ver:
            max_ver = ver_num

    next_ver_str = str(max_ver + 1).zfill(4)
    return next_ver_str


def _get_project(project_name):

    if project_name in PROJECT_MAP:
        return PROJECT_MAP[project_name]


    proj_info = edbc.calls('edbc.find', 'Project', [['name', 'is',  project_name]], [])
    if not proj_info:
        print('Error: invalid project')
        sys.exit(ERR_INVALID_PROJECT)

    proj_info = proj_info[0]
    print('Project OK: {} - {}'.format(project_name, proj_info))
    
    if project_name not in PROJECT_MAP:
        PROJECT_MAP[project_name] = proj_info


    return proj_info


def _dist_sset_int(sset_src_root, sset_dest_zip_path, sset_name, release_num):

    if not os.path.isdir(sset_src_root):
        print('Error: dir not found: {}'.format(sset_src_root))
        print('aborting')
        # sys.exit(ERR_SSET_NOT_FOUND)
        return


    dest_zip_dir, dest_zip_filename = os.path.split(sset_dest_zip_path)
    # fs_root = os.getenv('RLP_FS_ROOT')
    # inst_root = os.path.dirname(sset_dest_path)

    # os.path.join(
    #     fs_root, SITE_NAME, 'release', PLATFORM, 'dist', 'proj', project_name, 'sset')
    
    if not os.path.isdir(dest_zip_dir):
        print('Creating {}'.format(dest_zip_dir))
        os.makedirs(dest_zip_dir)


    # sset_inst_root = os.path.join(inst_root, dest_sset_path, release_num)
    # sset_src_root = os.path.join(os.path.dirname(args.config_path), sset_name)


    
    # if not os.path.isdir(sset_inst_root):
    #     print('Creating {}'.format(sset_inst_root))
    #     os.makedirs(sset_inst_root)

    release_num_str = str(release_num).zfill(4)
    # next_ver_str = _get_next_ver(sset_inst_root, sset_name)

    print('next version: {}'.format(release_num_str))

    # print('CONFIG:')
    # print(sset_config)


    
    # 'sset_{}_{}_{}.7z'.format(
    #     sset_name, sset_config['sftset_version'], next_ver_str)

    temp_filename = os.path.join(tempfile.gettempdir(), dest_zip_filename)

    if os.path.isfile(temp_filename):
        print('Cleaning {}'.format(temp_filename))
        os.remove(temp_filename)


    # hmm.. need to start the archive with the release number directory..
    # make a temp area with the release number, copy everything into it
    # and archive that..
    tempdir = tempfile.mkdtemp(prefix='{}_'.format(sset_name))
    temp_release_dir = os.path.join(tempdir, release_num_str)
    # os.mkdir(temp_release_dir)

    
    print('{} -> {}'.format(sset_src_root, temp_release_dir))

    shutil.copytree(sset_src_root, temp_release_dir)

    cmd = '{} a {} {}'.format(ZCMD, temp_filename, temp_release_dir)

    print(cmd)
    r = subprocess.run(cmd, shell=True)

    # if not os.getenv('RLP_FS_ROOT'):
    #     print('ERROR: RLP_FS_ROOT not set')
    #     raise Exception('stop')

    # sset_dest_path = os.path.join(sset_inst_root, sset_filename)
    
    cp_cmd = '{} {} {}'.format(CPCMD, temp_filename, sset_dest_zip_path)

    print('')
    print('DONE')
    print('')
    print(cp_cmd)
    r = subprocess.run(cp_cmd, shell=True)
    print(r)

    if r.returncode != 0:
        print('ERROR DOING COPY, ABORT')
        return


def _dist_sset_tb(args, sset_name, sset_config, release_num):
    print('DIST THIRDBASE SSET')

    tb_version = sset_config['sftset_version']
    tb_dir = os.path.join(TB_ROOT, tb_version, PLATFORM)

    fs_root = os.getenv('RLP_FS_ROOT')
    rfs_tb_dir = os.path.join(fs_root, SITE_NAME, 'release', PLATFORM, 'thirdbase')

    for tb_project in sset_config['flavour']['default']:
        print(tb_project)
        zip_filename = '{}.7z'.format(tb_project['version'])

        zip_src_path = os.path.join(tb_dir, tb_project['name'], zip_filename)
        zip_dest_dir = os.path.join(rfs_tb_dir, tb_project['name'])
        if not os.path.isdir(zip_dest_dir):
            os.makedirs(zip_dest_dir)
        
        zip_dest_path = os.path.join(zip_dest_dir, zip_filename)

        if not os.path.isfile(zip_src_path):
            print('NOT FOUND: {}'.format(zip_src_path))
            continue
        
        if os.path.isfile(zip_dest_path):
            print('Skipping: {}'.format(zip_dest_path))
            continue

        cp_cmd = '{} {} {}'.format(CPCMD, zip_src_path, zip_dest_path)
        print(cp_cmd)
        
        # continue


        r = subprocess.run(cp_cmd, shell=True)
        print(r)
        if r.returncode != 0:
            print('ERROR DOING COPY')





def release_sset(args):

    sset_name = args.sset

    sset_config = None
    with open(args.config_path) as fh:
        build_info = json.load(fh)
        sset_config = build_info[sset_name]


    proj_info = edbc.calls('edbc.find', 'Project', [['name', 'is',  args.project]], [])
    if not proj_info:
        print('Error: invalid project')
        sys.exit(ERR_INVALID_PROJECT)

    proj_info = proj_info[0]
    print('Project OK: {} - {}'.format(args.project, proj_info))


    sset_release_info = edbc.calls('edbc.find', 'SoftwareSetRelease',
        [
            ['project', 'is', proj_info],
            ['sset_name', 'is', sset_name],
            ['sset_version', 'is', sset_config['sftset_version']]
        ],
        ['sset_release_num']
    )

    max_num = 0
    for sset_rel_entry in sset_release_info:
        print('GOT {}'.format(sset_rel_entry))
        print('')
        if sset_rel_entry['sset_release_num'] > max_num:
            max_num = sset_rel_entry['sset_release_num']

    max_num += 1

    if sset_config['sftset_type'] != 'ext':
        zip_build(args)

    print(sset_release_info)
    print('Creating SoftwareSetRelease {} {}'.format(sset_name, max_num))

    # print(json.dumps(sset_config.get('bin_public', '')))
    edbc.calls('edbc.create', 'SoftwareSetRelease', '', {
        'project': proj_info,
        'name': '{}.{}.{}.{}'.format(args.project, sset_name, sset_config['sftset_version'], max_num),
        'sset_name': sset_name,
        'sset_type': sset_config['sftset_type'],
        'sset_version': sset_config['sftset_version'],
        'sset_release_num': max_num,
        'sset_config': json.dumps(sset_config)
    }, '')

    return max_num


def release_build(args):

    print('RELEASE BUILD')
    print('Site: {}'.format(args.site))
    print('Project: {}'.format(args.project))


    os.environ['RLP_SITE'] = args.site


    proj_info = edbc.calls('edbc.find', 'Project', [['name', 'is',  args.project]], [])
    if not proj_info:
        print('Error: invalid project')
        sys.exit(ERR_INVALID_PROJECT)

    proj_info = proj_info[0]
    print('Project OK: {} - {}'.format(args.project, proj_info))

    max_version = 0
    if args.version:
        max_version = args.version

    else:
        for entry in build_version_info:
            if entry['version_num'] > max_version:
                max_version = entry['version_num']

        max_version += 1

    build_version_str = str(max_version).zfill(3)

    print('Build Version: {}'.format(max_version))


    build_version_info = edbc.calls('edbc.find', 'BuildVersion',
        [
            ['project', 'is',  proj_info]
        ],
        ['version']
    )

    build_version_uuid = None


    # check if we already have a build version num..
    for bv_entry in build_version_info:
        if bv_entry['version'] == max_version:
            print('Found existing BuildVersion: {}'.format(bv_entry))
            build_version_uuid = bv_entry['uuid']
            break

    else:

        build_version_uuid = edbc.calls('edbc.create', 'BuildVersion', '', {
            'project': proj_info,
            'name': '{}.{}'.format(args.project, build_version_str),
            'version': build_version_str
        }, '')

        print('Created Build Version {} - {}'.format(max_version, build_version_uuid))


    assert(build_version_uuid)
    bv_info = {'et_name': 'BuildVersion', 'uuid': build_version_uuid}

    build_info = None
    with open(args.config_path) as fh:
        build_info = json.load(fh)

        for sset_name, sset_build_info in build_info.items():

            sset_build_info['sftset_name'] = sset_name

            if sset_name == '__bootstrap__':
                sset_build_info['project'] = args.project
                sset_build_info['build_version'] = build_version_str
                continue

            # if sset_build_info.get('sftset_type') not in ['int', 'ext', 'app']:
            #    continue
            
            print('Checking {}'.format(sset_build_info))
            sset_e_info = edbc.calls('edbc.find', 'BuildSoftwareSet',
                [
                    ['sset_name', 'is', sset_name],
                    ['build_version', 'is', bv_info]
                ],
                ['sset_release']
            )

            if not sset_e_info:
                print('No BuildSoftwareSet found for "{}", creating'.format(sset_name))
                sset_uuid = edbc.calls('edbc.create', 'BuildSoftwareSet', '', {
                    'name': '{}.{}'.format(args.project, sset_name),
                    'sset_name': sset_name,
                    'build_version': bv_info
                }, '')
                sset_e_info = [{'et_name': 'BuildSoftwareSet', 'uuid': sset_uuid}]


            elif len(sset_e_info) != 1:
                print('INVALID RESULT, EXPECTED 1, GOT {}'.format(len(sset_e_info)))
                return

            
            sset_e_info = sset_e_info[0]
            print(sset_e_info)
            # if sset_e_info.get('sset_release'):


            
            # print(sset_uuid)

            # Merge in release version info..
            #

            '''
            elif len(sset_e_info) != 1:
                raise Exception('ERROR: multiple results - {}'.format(sset_build_info))
                print(sset_build_info)
                sset_uuid = sset_build_info[0]['uuid']

                result = edbc.calls('edbc.deleteEntity', 'SoftwareSet', sset_uuid)
                print(result)
            '''
        


    temp_fd, tempfilename = tempfile.mkstemp(prefix='sc_config_', suffix='.json')
    os.close(temp_fd)
    with open(tempfilename, 'w') as wfh:
        wfh.write(json.dumps(build_info, indent=2))

    print('Wrote {}'.format(tempfilename))

    _copy_build_description(args.project, tempfilename, args.version)



def _get_build_description_inst_path(project, build_version, mkdirs=False):

    # Copy to versioned network location
    #
    fs_root = os.getenv('RLP_FS_ROOT')
    build_inst_root = os.path.join(
        fs_root, SITE_NAME, 'release', PLATFORM, 'dist', 'proj', project, 'build')

    build_filename = 'sc_config_{}.json'.format(str(build_version).zfill(3))
    build_inst_path =  os.path.join(build_inst_root, build_filename)

    if mkdirs and not os.path.isdir(build_inst_root):
        print('Creating {}'.format(build_inst_root))
        os.makedirs(build_inst_root)

    return build_inst_path


def _copy_build_description(project, build_src_path, build_version):

    
    build_inst_path = _get_build_description_inst_path(project, build_version, mkdirs=True)

    cp_cmd = '{} {} {}'.format(CPCMD, build_src_path, build_inst_path)
    print(cp_cmd)

    r = subprocess.run(cp_cmd, shell=True)
    print(r)

    if r.returncode != 0:
        print('ERROR DOING COPY, ABORT')
        return


def link_sset(args):
    print(args)

    proj_info = _get_project(args.project)
    sset_proj_info = proj_info
    if args.sset_project:
       sset_proj_info = _get_project(args.sset_project)

    sset_release_info = edbc.calls('edbc.find', 'SoftwareSetRelease',
        [
            ['project', 'is', sset_proj_info],
            ['sset_name', 'is', args.sset],
            ['sset_version', 'is', args.sset_version],
            ['sset_release_num', 'is', int(args.release_num)]
        ],
        []
    )

    if not sset_release_info or len(sset_release_info) != 1:
        print('Invalid result for sset_release_info, got {} results'.format(len(sset_release_info)))
        return

    sset_rel = {
        'et_name': 'SoftwareSetRelease',
        'uuid': sset_release_info[0]['uuid']
    }

    
    print('SoftwareSetRelease OK: {}'.format(sset_rel))
    
    build_info = edbc.calls('edbc.find', 'BuildVersion',
        [
            ['project', 'is',  proj_info],
            ['version', 'is', args.build_version]
        ],
        ['version', 'name']
    )
    if not build_info or len(build_info) != 1:
        print('Invalid result for BuildVersion, got {} results'.format(len(build_info)))
        pprint.pprint(build_info)

        return

    bv_info = build_info[0]

    build_sset_info = edbc.calls('edbc.find', 'BuildSoftwareSet',
        [
            ['sset_name', 'is', args.sset],
            ['build_version', 'is', bv_info]
        ],
        []
    )

    if not build_sset_info or len(build_sset_info) != 1:
        print('Invalid result for BuildSoftwareSet, got {} results'.format(len(build_sset_info)))
        return

    b_sset_info = build_sset_info[0]

    print(b_sset_info)

    print('OK - Linking')

    result = edbc.calls('edbc.update', 'BuildSoftwareSet', b_sset_info['uuid'],
        {
            'sset_release': sset_rel
        })
    
    print(result)


    build_inst_path = _get_build_description_inst_path(
        args.project, args.build_version)

    print('Serializing link into build description: {}'.format(build_inst_path))
    assert(os.path.isfile(build_inst_path))


    print('Loading {}'.format(build_inst_path))

    build_config = None
    with open(build_inst_path) as fh:
        build_config = json.load(fh)


    for sset_name, sset_config in build_config.items():
        if sset_name == args.sset:
            sset_config['release_num'] = int(args.release_num)

    temp_fd, tempfilename = tempfile.mkstemp(prefix='sc_config_', suffix='.json')
    os.close(temp_fd)
    with open(tempfilename, 'w') as wfh:
        wfh.write(json.dumps(build_config, indent=2))

    print('Wrote {}'.format(tempfilename))

    _copy_build_description(args.project, tempfilename, args.build_version)


def _get_next_sset_release_num(project_name, sset_name, sset_version):

    project_info = _get_project(project_name)

    sset_release_info = edbc.calls('edbc.find', 'SoftwareSetRelease',
        [
            ['project', 'is', project_info],
            ['sset_name', 'is', sset_name],
            ['sset_version', 'is', sset_version]
        ],
        ['sset_release_num']
    )

    max_num = 0
    for entry in sset_release_info:
        print(entry)
        if entry['sset_release_num'] > max_num:
            max_num = entry['sset_release_num']

    return max_num + 1


def zip_build(args):

    build_info = None
    with open(args.config_path) as fh:
        build_info = json.load(fh)


    if not build_info:
        print('Invalid build info, aborting')
        return

    build_info['__bootstrap__']['project'] = args.project
    sset_mgr = SoftwareSetManager(build_info, args.config_path)

    zip_src_obj = sset_mgr
    if args.sset:
        zip_src_obj = sset_mgr.get_software_set(args.sset)


    localize_list = zip_src_obj.get_all()


    for entry in localize_list:

        if args.release_num:
            next_release_num = int(args.release_num)
            entry.set_release_num(next_release_num)

        elif not entry.has_release():
            print('WARNING: No release for {}, getting new release num'.format(entry.name))
            next_release_num = _get_next_sset_release_num(args.project, entry.name, entry.sftset_version)
            print('Got next release num: {}'.format(next_release_num))
            entry.set_release_num(next_release_num)

        zip_network_path = Path(entry.zip_uri).format(translation_map='network')
        
        if not os.path.isfile(zip_network_path):
            print('Zip creation required: {}'.format(zip_network_path))

            base_dir = str(entry.base_dir)
            pprint.pprint(entry.config)
            if entry.sftset_type == 'int':
                _dist_sset_int(base_dir, zip_network_path, entry.name, next_release_num)

            else:
                
                if not os.path.isdir(base_dir):
                    print('ERROR: SOURCE DIR NOT FOUND: {}'.format(base_dir))
                    continue
        
                zip_filename_prefix = '{}_'.format(entry.name.replace('/', '_'))
                temp_fd, temp_filename = tempfile.mkstemp(
                    prefix=zip_filename_prefix, suffix='.7z')
                os.close(temp_fd)
                os.remove(temp_filename)

                zip_cmd = '{} a {} {}'.format(ZCMD, temp_filename, base_dir)
                print(zip_cmd)

                # continue
                r = subprocess.run(zip_cmd, shell=True)
                if r.returncode == 0:
                    assert(os.path.isfile(temp_filename))

                    network_parent_dir = os.path.dirname(zip_network_path)
                    if not os.path.isdir(network_parent_dir):
                        print('Creating {}'.format(network_parent_dir))
                        os.makedirs(network_parent_dir)

                    cp_cmd = '{} {} {}'.format(CPCMD, temp_filename, zip_network_path)
                    print(cp_cmd)

                    r = subprocess.run(cp_cmd, shell=True)
                    if r.returncode != 0:
                        print('ERROR DOING COPY: {}'.format(r))

                    print('Cleaning {}'.format(temp_filename))
                    os.remove(temp_filename)

        else:
            print('Zip OK: {}'.format(zip_network_path))


def print_info(args):

    from scaffold.env.sset_mgr import SoftwareSetManager

    # path = '/home/justinottley/dev/revlens_root/sp_project/inst/Linux/sc_config.json'
    # path = '/home/justinottley/dev/revlens_root/fs/fuse_root/rlp_test/release/Linux-x86_64/dist/proj/stickman/build/sc_config_002.json'
    path ='/home/justinottley/dev/revlens_root/sp_revsix/sc_config_002.json'

    print(path)
    build_info = None
    with open(path) as fh:
        build_info = json.load(fh)

    build_info['__bootstrap__']['project_name'] = 'stickman'
    mgr = SoftwareSetManager(build_info, path)
    print(mgr)
    print(mgr._software_sets)

    for entry in mgr._software_sets.values():
        print(entry.name)
        if entry.name == 'maya':
            continue
        ir = entry.get_install_required()
        print(ir)


    return


    print('PRINT INFO')
    def _print_result(result):

        print(result)
        for entry in result:
            print(entry)


    edbc.call(_print_result, 'edbc.find', 'App', [], ['version']).run()

