
import os

from .. import ThirdbaseLib
from ... import util as buildsys_util

class OpenSSLLib(ThirdbaseLib):

    def init(self, benv):

        env = benv.env


class PosixOpenSSLLib(OpenSSLLib):

    def init(self, benv):
        OpenSSLLib.init(self, benv)

        env = benv.env

        env['LIBS'].extend([
            'ssl',
            'crypto'
        ])


PLATFORM_MAP = \
[
    {'variants':{'opsys':'Linux'},
     'result': PosixOpenSSLLib},
    {'variants':{'opsys':'Darwin'},
     'result': PosixOpenSSLLib},
]
