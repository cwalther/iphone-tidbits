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

import struct
import PIL.Image # You must have the Python Imaging Library (PIL) installed

from .binary_file import BinaryFile

class ArtworkBinaryFile(BinaryFile):
    """Represents an iOS SDK .artwork file"""
    
    WIDTH_BYTE_PACKING = 8 # Determined by inspection/luck.
    
    def __init__(self, filename):
        super(ArtworkBinaryFile, self).__init__(filename)
        
    @staticmethod
    def _align(offset):
        """Perform packing alignment appropriate for image pixels in the .artwork file"""
        remainder = offset % ArtworkBinaryFile.WIDTH_BYTE_PACKING
        if remainder != 0: offset += (ArtworkBinaryFile.WIDTH_BYTE_PACKING - remainder)
        return offset        

    def get_pil_image(self, width, height, offset):
        pil_image = PIL.Image.new("RGBA", (width, height))
        pil_pixels = pil_image.load()

        aligned_width = ArtworkBinaryFile._align(width)

        for y in range(height):
            for x in range(width):
                pixel_offset = offset + (4 * ((y * aligned_width) + x))
                b, g, r, a = struct.unpack_from('<BBBB', self.data, pixel_offset)
                pil_pixels[x, y] = (r, g, b, a)
                
        return pil_image        

    