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

from .macho_file import MachOBinaryFile
from .structs import ArtworkSetInformation

class UIKitBinaryFile(MachOBinaryFile):
    """Represents the UIKit framework binary, with special tools to look for artwork."""

    def __init__(self, filename):
        super(MachOBinaryFile, self).__init__(filename)
        
    @property
    def images_offset(self):
        return self.find_symbol("___images")
    
    @property
    def mapped_images_offset(self):
        return self.find_symbol("___mappedImages")
        
    @property
    def shared_images_offset(self):
        # TODO return self.find_symbol("___sharedImages")
        return None
        
    @property
    def shared_iphone_image_sets_offset(self):
        return self.find_symbol("___sharedImageSetsPhone")
        
    @property
    def shared_ipad_image_sets_offset(self):
        return self.find_symbol("___sharedImageSetsPad")
        
    @property
    def shared_image_sets_count(self):
        # TODO: this doesn't work? shared_image_sets_offset = self.find_symbol("___sharedImageSetsCount")
        return 2

    def read_artwork_set_information(self, offset):
        return ArtworkSetInformation(self.default_endian, self.data, offset)

    def iter_shared_iphone_image_sets(self):
        offset = self.shared_iphone_image_sets_offset
        for artwork_set_i in range(self.shared_image_sets_count):
            yield self.read_artwork_set_information(offset)
            offset += ArtworkSetInformation.SIZE

    def iter_shared_ipad_image_sets(self):
        offset = self.shared_ipad_image_sets_offset
        for artwork_set_i in range(self.shared_image_sets_count):
            yield self.read_artwork_set_information(offset)
            offset += ArtworkSetInformation.SIZE

