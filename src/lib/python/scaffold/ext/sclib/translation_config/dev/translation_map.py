
import os
if not os.getenv('RLP_SITE'):
    os.environ['RLP_SITE'] = ''

name = 'local'

translation_map = [
    {
        'name': 'thirdbase',
        'mapping': {
            'DriveLetter': ['$HOMEDRIVE', '$HOMEPATH', 'dev', 'revlens_root', 'thirdbase', '$SC_THIRDBASE_VERSION', '$SC_PLATFORM'],
            'UNC': ['rlp', '$RLP_SITE', 'thirdbase', '$SC_THIRDBASE_VERSION', '$SC_PLATFORM'],
            'Posix': ['$HOME', 'dev', 'revlens_root', 'thirdbase', '$SC_THIRDBASE_VERSION', '$SC_PLATFORM'],
            'URI': ['thirdbase']
        }
    },
    {
        'name': 'apps',
        'mapping': {
            'DriveLetter': ['$HOMEDRIVE', '$HOMEPATH', '.config', 'rlp', 'release', '$SC_PLATFORM', 'apps'],
            'UNC': ['rlp', '$RLP_SITE', 'release', '$SC_PLATFORM', 'apps'],
            'Posix': ['$HOME', '.config', 'rlp', '$RLP_SITE', 'release', '$SC_PLATFORM', 'apps'],
            'URI': ['apps']
        }
    },
    {
        'name': 'dist',
        'mapping':{
            'DriveLetter': ['$HOMEDRIVE', '$HOMEPATH', '.config', 'rlp', 'release', '$SC_PLATFORM', 'dist'],
            'UNC': ['rlp', '$RLP_SITE', 'release', '$SC_PLATFORM', 'dist'],
            'Posix': ['$HOME', '.config', 'rlp', '$RLP_SITE', 'release', '$SC_PLATFORM', 'dist'],
            'URI':['dist']
        }
    }
]

