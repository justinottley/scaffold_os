
name = 'network'

translation_map = [
    {
        'name': 'thirdbase',
        'mapping': {
            'DriveLetter': ['R:', '$RLP_SITE', 'release', '$SC_PLATFORM', 'thirdbase', '$SC_THIRDBASE_VERSION'],
            'UNC': ['rlp', '$RLP_SITE', 'release', '$SC_PLATFORM', 'thirdbase', '$SC_THIRDBASE_VERSION'],
            'Posix': ['$RLP_FS_ROOT', '$RLP_SITE', 'release', '$SC_PLATFORM', 'thirdbase', '$SC_THIRDBASE_VERSION'],
            'RFS': ['$RLP_SITE', 'thirdbase', '$SC_THIRDBASE_VERSION', '$SC_PLATFORM'],
            'URI': ['thirdbase']
        }
    },
    {
        'name': 'apps',
        'mapping': {
            'DriveLetter': ['R:','$RLP_SITE', 'release', '$SC_PLATFORM', 'apps'],
            'UNC': ['rlp', '$RLP_SITE', 'release', '$SC_PLATFORM', 'apps'],
            'Posix': ['$RLP_FS_ROOT', '$RLP_SITE', 'release', '$SC_PLATFORM', 'apps'],
            'RFS': ['$RLP_SITE', 'release', '$SC_PLATFORM', 'apps'],
            'URI': ['apps']
        }
    },
    {
        'name': 'dist',
        'mapping':{
            'DriveLetter': ['R:','$RLP_SITE', 'release', '$SC_PLATFORM', 'dist'],
            'UNC': ['rlp', '$RLP_SITE', 'release', '$SC_PLATFORM', 'dist'],
            'Posix': ['$RLP_FS_ROOT', '$RLP_SITE', 'release', '$SC_PLATFORM', 'dist'],
            'RFS': ['$RLP_SITE', 'release', '$SC_PLATFORM', 'dist'],
            'URI':['dist']
        }
    },
    {
        'name':'proj',
        'mapping': {
            'DriveLetter': ['R:','$RLP_SITE', 'proj'],
            'UNC': ['rlp', '$RLP_SITE', 'proj'],
            'Posix': ['$RLP_FS_ROOT', '$RLP_SITE', 'proj'],
            'RFS': ['$RLP_SITE', 'proj'],
            'URI': ['proj']
        }
    },
    {
        'name': 'users',
        'mapping': {
            'DriveLetter': ['R:', '$RLP_SITE', 'users'],
            'UNC': ['rlp', '$RLP_SITE', 'users'],
            'Posix': ['$RLP_FS_ROOT', '$RLP_SITE', 'users'],
            'RFS': ['$RLP_SITE', 'proj'],
            'URI': ['users']
        }
    }
]

