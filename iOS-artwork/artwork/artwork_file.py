#-------------------------------------------------------------------------------
#
# iOS .artwork file extractor
# (c)2008-2011 Dave Peck <code [at] davepeck [dot] org> All Rights Reserved
# 
# Released under the three-clause BSD license.
#
# http://github.com/davepeck/iphone-tidbits/
#
#-------------------------------------------------------------------------------

from .binary_file import BinaryFile

class ArtworkBinaryFile(BinaryFile):
    """Represents an iPhone SDK .artwork file"""
    def __init__(self, filename):
        super(ArtworkBinaryFile, self).__init__(filename)
