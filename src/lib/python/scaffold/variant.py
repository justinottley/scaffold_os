'''
#
# Copyright 2014-2024 Justin Ottley
#
# Licensed under the terms set forth in the LICENSE.txt file
#

Provides a flexible platform string solution for multiflavour build systems,
including all the platform info relevant for building software in a
human readable format.

Additionally, runtime registration of arbitrary variants to be included
in the platform string is available. Things like compiler or build flavour
can be included in the platform string using variant registration.

Registration of variants is order-preserving, so that the variant values can be
changed to get a consistently named platform / variant string across multiple
builds. Variant parts are separated in the platform string by dashes by default.

Variants can be grouped, and variant groups become directories to achieve
subdirectory trees of variants, assuming you leave the group separator
as the os directory path separator.

An example base platform string for CentOS 6.5 might look like:

>>> get_platform()
'Linux-x86_64-CentOS_6.5'


inclusion of a "compiler" variant:

>>> register_variant('compiler', 'clang_5.1')
'Linux-x86_64-CentOS_6.5-clang_5.1'


changing the 'compiler' variant:

>>> register_variant('compiler', 'gcc_4.2')
'Linux-x86_64-CentOS_6.5-gcc_4.2'


create a new variant group:

>>> push_group()


set a compiler variant in the new group:

>>> register_variant('compiler', 'gcc_4.2')
'Linux-x86_64-CentOS_6.5/gcc_4.2'


change the compiler in the new variant group:

>>> register_variant('compiler', 'clang_5.1')
'Linux-x86_64-CentOS_6.5/clang_5.1'

'''

import os
import socket
import platform
import traceback
from collections import OrderedDict

_platform_manager = None

VARIANT_TYPE_PLATFORM = 'platform'
VARIANT_TYPE_OPTIONAL = 'optional'
VARIANT_TYPE_OPSYS_VERSION = 'opsys_version'

    
class ScaffoldVariantException(Exception): pass

class PlatformManager(object):
    '''
    handles the construction of a platform string.
    '''
    
    # A mapping for handling multple compatible platforms more easily
    #
    # Example: 
    # 'Linux-x86_64-CentOS_Linux_7.4.1708': 'Linux-x86_64-CentOS_Linux_7.3.1611'
    
    _PLATFORM_MAP = {}
    
    def __init__(self, sep='-', group_sep=os.path.sep):
        
        self._opsys_ver_major = False
        self._opsys_ver_minor = False
        self._opsys_ver_patch = False

        self._init_opsys_ver_defaults()

        self.variants = OrderedDict()
        
        self.__sep = sep
        self.__group_sep = group_sep
        
        self.variants['opsys'] = {'name':platform.system(),
                                  'type':VARIANT_TYPE_PLATFORM}
                                  
        self.variants['arch'] = {'name':platform.machine(),
                                 'type':VARIANT_TYPE_PLATFORM}
        
        
        vc_ver_info = self._get_vc_version()
        if len(vc_ver_info) == 5:
            
            self.variants['vc_version.full'] = {
                'name': vc_ver_info[0],
                'type': VARIANT_TYPE_OPTIONAL
            }
            
            self.variants['vc_version.minor_full'] = {
                'name': vc_ver_info[1],
                'type': VARIANT_TYPE_OPTIONAL
            }
            
            
        
        self.group_idx_list = []
        
        try:
            ver_major, ver_minor, ver_patch = getattr(
                self, '_get_opsys_version_{base_platform}'.format(
                    base_platform=self.variants['opsys']['name'].lower()))()
                    
            self.variants['opsys_version.major'] = {
                'name': ver_major,
                'type':VARIANT_TYPE_OPSYS_VERSION
            }

            self.variants['opsys_version.minor'] = {
                'name': ver_minor,
                'type': VARIANT_TYPE_OPSYS_VERSION
            }
            
            self.variants['opsys_version.patch'] = {
                'name': ver_patch,
                'type': VARIANT_TYPE_OPSYS_VERSION
            }


        except Exception as e:
            raise ScaffoldVariantException(
                'unsupported base OS - "{base_os}" {exc} : {message}'.format(
                    base_os=self.variants['opsys']['name'],
                    exc=e.__class__.__name__, message=str(e)))
            
        
        
        self.variants['hostname'] = {'name':socket.gethostname(),
                                     'type':VARIANT_TYPE_OPTIONAL}
        
        
    def _init_opsys_ver_defaults(self):

        if platform.system() == 'Darwin':
            self._opsys_ver_major = True
            self._opsys_ver_minor = True

        elif os.name == 'nt':
            self._opsys_ver_major = True


    def _get_vc_version(self):
        
        path = __file__
        for x in range(6):
            path = os.path.dirname(path)
        
        vc_version = os.path.basename(path)
        
        result = []
        
        try:
            vc_version_parts = vc_version.split('.')
            if len(vc_version_parts) == 3:
                ver_major = vc_version_parts[0]
                ver_minor = vc_version_parts[1]
                ver_patch = vc_version_parts[2]
                
                ver_minor_full = '.'.join(vc_version_parts[0:2])
                
                result = [vc_version, ver_minor_full, ver_major, ver_minor, ver_patch]
            
        except:
            print(traceback.format_exc())
            
            
        return result
        
        
    def _get_opsys_version_linux(self):
    	
        if hasattr(platform, "linux_distribution"):
            (dist_name, opsys_version, dist_id) = platform.linux_distribution()
        else:
            plat_info = platform.uname()
            dist_name = plat_info.system
            opsys_version = plat_info.release
            dist_id = ""
            
        try:
            ver_parts = opsys_version.split('.')
            ver_major = ver_parts[0]
            ver_minor = ''
            ver_patch = ''

            if len(ver_parts) > 1:
                ver_minor = ver_parts[1]

            if len(ver_parts)> 2:
                ver_patch = ver_parts[2]

            ver_major = '{dn}_{ver}'.format(
                dn=dist_name.replace(' ', '_'),
                ver=ver_major
            )
        except:
            print('Warning: could not get major, minor, patch versions from opsys version {v}'.format(v=opsys_version))
            print(traceback.format_exc())

            ver_major = opsys_version

        
        return (ver_major, ver_minor, ver_patch)
        
        
    def _get_opsys_version_darwin(self):
        '''
        Mac OSX
        '''
        
        (opsys_version, _, _) = platform.mac_ver()
        try:
            ver_parts = opsys_version.split('.')
            ver_major = ver_parts[0]
            ver_minor = ver_parts[1]
            ver_patch = ''
            if len(ver_parts) > 2:
                ver_patch = ver_parts[2]

        except:
            print('Warning: could not get major, minor, patch versions from opsys version {v}'.format(v=opsys_version))

            ver_major = opsys_version
            ver_minor = ''
            ver_patch = ''

        return (ver_major, ver_minor, ver_patch)
        
        
    def _get_opsys_version_windows(self):
        
        opsys_version_info = platform.win32_ver()
        try:
            ver_major, ver_minor, ver_patch = opsys_version_info[1].split('.')
            if opsys_version_info[0] in ['post2008Server', '7']:
                print('scaffold.variant: WARNING: mapping Windows version "{}" -> "10"'.format(
                    opsys_version_info[0]))
                ver_major = '10'
            
        except:
            print('Warning: could not get major, minor, patch versions from opsys version {v}'.format(v=opsys_version))


        return (ver_major, ver_minor, ver_patch)


    def _get_opsys_version_emscripten(self):
        return ('1', '0', '0')


    def push_group(self):
        self.group_idx_list.append(len(self.variants))
        
    
    
    def _get_platform_opsys_version(self, major=None, minor=None, patch=None):
        
        platform_parts = []
        if major or (os.getenv('SCAFFOLD_VARIANT_OPSYS_VER_MAJOR') == '1') or self._opsys_ver_major:
            platform_parts.append(self.variants['opsys_version.major']['name'])

        if minor or (os.getenv('SCAFFOLD_VARIANT_OPSYS_VER_MINOR') == '1') or self._opsys_ver_minor:
            platform_parts.append(self.variants['opsys_version.minor']['name'])

        if patch or (os.getenv('SCAFFOLD_VARIANT_OPSYS_VER_PATCH') == '1') or self._opsys_ver_patch:
            platform_parts.append(self.variants['opsys_version.patch']['name'])

        return '.'.join(platform_parts)

    
    def _get_platform_raw(self, major=None, minor=None, patch=None):
        
        group_idx_list = [len(self.variants)]
        if self.group_idx_list:
            group_idx_list = self.group_idx_list + group_idx_list
            
        
        curr_group_idx = 0
        group_items = []
        for group_idx in group_idx_list:
            
            group_items.append(
                self.__sep.join([variant['name'] for variant in \
                    list(self.variants.values())[curr_group_idx:group_idx] \
                if variant['type'] == VARIANT_TYPE_PLATFORM]))
            
            curr_group_idx = group_idx
            
        platform_str =  self.__group_sep.join(group_items)
        platform_opsys_ver = self._get_platform_opsys_version(major, minor, patch)
        platform_list = [platform_str]
        if platform_opsys_ver:
            platform_list.append(platform_opsys_ver)
        platform_result = '-'.join(platform_list)
        
        return platform_result
        

    
    def _get_platform_mapped(self, major=None, minor=None, patch=None):
        
        platform = self._get_platform_raw(major, minor, patch)
        if platform in self._PLATFORM_MAP:
            platform = self._PLATFORM_MAP[platform]
        
        return platform


    @property
    def platform(self):
        '''
        a full platform string including all platform variants, 
        with groups separated by the group separator
        '''
        return self._get_platform_mapped()


def register_variant(variant, value, variant_type=VARIANT_TYPE_PLATFORM):
    '''
    register a variant to be included in the platform string
    '''
    
    global _platform_manager
    assert(_platform_manager)
    
    _platform_manager.variants[variant] = {'name':value, 'type':variant_type}
    
    
def get_platform(major=None, minor=None, patch=None, mapped=True):
    '''
    Get a platform string, including all registered variants
    
    The platform may be mapped to a different value to homogenize compatible
    platforms. Use mapped=False to get the actual, non-mapped platform string
    '''
    
    global _platform_manager
    assert(_platform_manager)
    
    if 'platform_target' in _platform_manager.variants:
        return _platform_manager.variants['platform_target']['name']

    elif mapped:
        return _platform_manager._get_platform_mapped(major, minor, patch)
        
    else:
        return _platform_manager._get_platform_raw(major, minor, patch)
    

def get_platform_list():

    return [
        get_platform(major=True, minor=True, patch=True),
        get_platform(major=True, minor=True, patch=False),
        get_platform(major=True, minor=False, patch=False),
        get_platform(major=False, minor=False, patch=False),
        platform.system()
    ]


def get_variant(variant, name=True):
    
    global _platform_manager
    assert(_platform_manager)
    
    if name:
        return _platform_manager.variants[variant]['name']
        
    return _platform_manager.variants[variant]
    
    
def get_variants():
    
    global _platform_manager
    assert(_platform_manager)
    
    return _platform_manager.variants.keys()
    
    
def push_group():
    
    global _platform_manager
    assert(_platform_manager)
    
    return _platform_manager.push_group()
    
    
def match(input_variants):
    '''
    For an input variant dict, determine whether all the mappings
    correpond to the current platform variants.
    example input : {'opsys':'Linux', 'arch':'x86_64'}
    '''
    
    global _platform_manager
    assert(_platform_manager)
    
    result = True
    
    
    for variant_name, variant_value in input_variants.items():
        if variant_name not in _platform_manager.variants or \
        variant_value != _platform_manager.variants[variant_name]['name']:
            
            result = False
            
            
    return result
    
    
def match_any(input_variant_list):
    '''
    If any of the input variants match, return True
    '''
    
    for entry in input_variant_list:
        if match(entry):
            return True
            
    return False
    
    
def match_result(input_variant_list):
    '''
    Take a list of input variants with a corresponding return result value,
    and return the input return value if a match is found against that group of
    input variants.
    
    example input: [{'variants':{'opsys':'Linux', 'arch':'x86_64'},
                     'result':'return result for Linux-x86_64'},
                    {'variants':{'opsys':'Windows', 'arch':'AMD32'},
                     'result':'return result for Windows-AMD32'}]
                     
    If the current platform is {opsys=Linux,arch=x86_64}, return value is
    "return result for Linux-x86_64"
    '''
    
    for input_variant_info in input_variant_list:
        if match(input_variant_info['variants']):
            return input_variant_info['result']
    
    
def get_python_version(minor=True, patch=False):
    '''
    Convenience function to return the current python version as a dot-delimited
    version string. The version format not including the patchlevel is the
    most common, for example used on the filesystem (on posix platforms anyway)
    as the parent for the site-packages directory.
    '''
    
    
    ver_tuple = platform.python_version_tuple()

    version_list = [ver_tuple[0]]
    if minor:
        version_list.append(ver_tuple[1])
    
    if patch:
        version_list.append(ver_tuple[2])

    return '.'.join(version_list)
    
    
def get_python_dirname(*args, **kwargs):
    '''
    Convenience function to return a "python directory name", just the word
    "python" followed by the python version. This format is the common
    directory naming convention for housing python's standard library and
    site-packages.
    '''
    
    return 'python{version}'.format(version=get_python_version(*args, **kwargs))
    
    
def _init_manager():
    
    global _platform_manager
    _platform_manager = PlatformManager()
    
    
_init_manager()
del _init_manager
