#
# Copyright 2014-2024 Justin Ottley
#
# Licensed under the terms set forth in the LICENSE.txt file
#

class PathError(Exception): pass
class PathFormatError(PathError): pass
class PathResolutionError(PathError): pass
