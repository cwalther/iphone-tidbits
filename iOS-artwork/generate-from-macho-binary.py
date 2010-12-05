#!/usr/bin/env python

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

# generate-from-macho-binary.py
#
# The code in this file is capable of grabbing the names, sizes, and offsets
# of all images in all (shared) artwork files.
#
# To run it, use:
#
#   ./generate-from-macho-binary.py /path/to/UIKit /output/directory/ 4.2.1
#
# More generally, use:
#
#   ./generate-from-macho-binary.py <macho-binary-file> <output-directory-file> <ios-version-number>
#
# In general, you shouldn't have to run this. I'll run it when new versions of the
# OS show up. 
#
# This code works by reading the mach-o header and symbol table from the UIKit
# binary, and then looking for special unexported symbols known to reference
# the names and size/offset information.  To use it, you must have the python
# macholib and PIL installed.

import os
import sys
import json

from artwork.uikit_file import UIKitBinaryFile
        
def process_artwork_set(artwork_set, uikit_directory_name, output_directory_name, version_string):
    """Generate a json file for a single artwork set found in the mach-o binary."""
    print "Found artwork set named %s" % artwork_set.name

    images_jsonable = []
    for artwork_name, artwork_size in artwork_set.iter_artworks():
        images_jsonable.append((artwork_name, artwork_size.width, artwork_size.height, artwork_size.offset))

    artwork_set_file_name = os.path.join(uikit_directory_name, "%s.artwork" % artwork_set.name)
    artwork_set_file_size = os.path.getsize(artwork_set_file_name)

    full_jsonable = {
        "name": os.path.basename(artwork_set_file_name),
        "version": version_string,
        "byte_size": artwork_set_file_size,
        "images": images_jsonable,
    }
    full_json = json.dumps(full_jsonable, indent = 4)
    
    images_file_name = os.path.join(output_directory_name, "%s.artwork-%d.json" % (artwork_set.name, artwork_set_file_size))
    images_file = open(images_file_name, "w")
    images_file.write(full_json)
    images_file.close()

def main():
    """Read command line options and extract image information. Currently only supports the UIKit binary."""
    uikit_file_name = os.path.abspath(sys.argv[1])
    uikit_directory_name = os.path.dirname(uikit_file_name)
    uikit = UIKitBinaryFile(uikit_file_name)
    
    output_directory_name = os.path.abspath(sys.argv[2])
    version_string = sys.argv[3]
    
    for artwork_set in uikit.iter_shared_iphone_image_sets():
        process_artwork_set(artwork_set, uikit_directory_name, output_directory_name, version_string)
    for artwork_set in uikit.iter_shared_ipad_image_sets():
        process_artwork_set(artwork_set, uikit_directory_name, output_directory_name, version_string)
    
if __name__ == "__main__":
    main()
