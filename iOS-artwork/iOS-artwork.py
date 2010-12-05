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

# iOS-artwork.py
#
# This script makes it easy to extract images from the .artwork files found
# in the iOS SDK. To use it, you must have python and the Python Imaging Libraries
# (PIL) installed.
#
# Run it as:
#
#   ./iOS-artwork.py export -a artwork_file.artwork -d export_directory
#
# You can also import a directory of images to create a new .artwork file:
#
#   ./iOS-artwork.py create -a original_artwork_file.artwork -d importDirectory -c created_artwork_file.artwork
#
# Please see the README.markdown file for more details.

import os
import sys
import json
from optparse import OptionParser

import PIL.Image

from artwork.artwork_file import ArtworkBinaryFile, WritableArtworkBinaryFile
    
COMMANDS = ["export", "create"]

class ArtworkInfo(object):
    def __init__(self, jsonable):
        super(ArtworkInfo, self).__init__()
        self.name = jsonable[0]
        self.width = jsonable[1]
        self.height = jsonable[2]
        self.offset = jsonable[3]

class ArtworkSetInfo(object):
    def __init__(self, jsonable):
        super(ArtworkSetInfo, self).__init__()
        self.name = jsonable["name"]
        self.version = jsonable["version"]
        self.byte_size = jsonable["byte_size"]
        self.images = jsonable["images"]
        
    @property
    def image_count(self):
        return len(self.images)
        
    def iter_images(self):
        for jsonable in self.images:
            yield ArtworkInfo(jsonable)

def usage(parser):
    parser.print_help()
    sys.exit(-1)

def bail(message):
    print "\n%s\n" % message
    sys.exit(-1)

def script_directory():
    return os.path.dirname(os.path.realpath(__file__))

def supported_artwork_files_directory():
    return os.path.join(script_directory(), "supported_artwork_files")

def supported_artwork_json_file_name(artwork_file_name):
    artwork_file_size = os.path.getsize(artwork_file_name)
    artwork_file_basename = os.path.basename(artwork_file_name)
    return os.path.join(supported_artwork_files_directory(), "%s-%d.json" % (artwork_file_basename, artwork_file_size))

def is_artwork_file_supported(artwork_file_name):
    supported_artwork = supported_artwork_json_file_name(artwork_file_name)
    return os.path.exists(supported_artwork)

def get_artwork_set_info(artwork_file_name):
    f = open(supported_artwork_json_file_name(artwork_file_name), "r")
    jsonable = json.loads(f.read())
    f.close()
    return ArtworkSetInfo(jsonable)

def file_extension(file_name):
    return os.path.splitext(file_name)[1][1:]
    
def action_export(artwork_file_name, directory):
    set_info = get_artwork_set_info(artwork_file_name)
    artwork_binary = ArtworkBinaryFile(artwork_file_name)
    
    print "\nExporting %d images from %s (version %s)..." % (set_info.image_count, set_info.name, set_info.version)
    
    for image_info in set_info.iter_images():
        pil_image = artwork_binary.get_pil_image(image_info.width, image_info.height, image_info.offset)
        export_file_name = os.path.join(directory, image_info.name)
        pil_image.save(export_file_name, file_extension(export_file_name))
        print "\texported %s" % export_file_name
        
    print "\nDONE!"
    
def action_create(artwork_file_name, directory, create_file_name):
    set_info = get_artwork_set_info(artwork_file_name)
    artwork_binary = ArtworkBinaryFile(artwork_file_name)
    create_binary = WritableArtworkBinaryFile(create_file_name, artwork_binary)
    create_binary.open()
    
    print "\nImporting %d images into new file named %s...\n\t(Using %s version %s as a template.)" % (set_info.image_count, create_file_name, set_info.name, set_info.version)
    
    for image_info in set_info.iter_images():
        #
        # Grab the image from disk
        #
        pil_image_name = os.path.join(directory, image_info.name)
        if not os.path.exists(pil_image_name):
            create_binary.delete()
            bail("FAIL. An image named %s was not found in directory %s" % (image_info.name, directory))
            
        #
        # Validate the image
        #
        try:
            pil_image = PIL.Image.open(pil_image_name)
        except IOError:
            create_binary.delete()
            bail("FAIL. The image file named %s was invalid or could not be read." % pil_image_name)
        
        actual_width, actual_height = pil_image.size
        if (actual_width != image_info.width) or (actual_height != image_info.height):
            create_binary.delete()
            bail("FAIL. The image file named %s should be %d x %d in size, but is actually %d x %d." % (pil_image_name, image_info.width, image_info.height, actual_width, actual_height))
        
        try:
            if (pil_image.mode != 'RGBA') and (pil_image.mode != 'RGB'):
                pil_image = pil_image.convert('RGBA')
        except:
            create_binary.delete()
            bail("FAIL. The image file named %s could not be converted to a usable format." % pil_image_name)
        
        #
        # Write it
        #
        create_binary.write_pil_image(image_info.width, image_info.height, image_info.offset, pil_image)
        print "\timported %s" % image_info.name
    
    create_binary.close()
    
    print "\nDONE!"
    
def main(argv):
    #
    # Set up command-line options parser
    #
    parser = OptionParser(usage = """%prog [command] [parameters]

    export 
        -a artwork_file.artwork 
        -d export_directory
    
        Exports the contents of artwork_file.artwork as a set
        of images in the export_directory
    
    import  
        -a original_artwork_file.artwork 
        -d import_directory 
        -c created_artwork_file.artwork
         
        Imports the images found in import_directory into a new
        artwork file named created_artwork_file.artwork. Uses
        the original file for sizing and other information, but
        never writes to the original file.
    """)
    parser.add_option("-a", "--artwork", dest="artwork_file_name", help="Specify the input artwork file name. (Read-only.)", default = None)
    parser.add_option("-d", "--directory", dest="directory", help="Specify the directory to export images to/import images from.", default = None)
    parser.add_option("-c", "--create", dest="create_file_name", help="Specify the output artwork file name. (Write-only.)", default = None)

    #
    # Parse
    #
    (options, arguments) = parser.parse_args()
    
    #
    # Validate
    #
    if (len(arguments) != 1) or (options.artwork_file_name is None) or (options.directory is None):
        usage(parser)
        
    command = arguments[0].lower()
    if command not in COMMANDS:
        usage(parser)
        
    if (command == "create") and (options.create_file_name is None):
        usage(parser)
        
    abs_artwork_file_name = os.path.abspath(options.artwork_file_name)
    
    if not os.path.exists(abs_artwork_file_name):
        bail("No artwork file named %s was found." % options.artwork_file_name)
        
    if not is_artwork_file_supported(abs_artwork_file_name):
        bail("Sorry, but the artwork file %s is not currently supported by this software." % options.artwork_file_name)
    
    abs_directory = os.path.abspath(options.directory)
    
    if not os.path.exists(abs_directory):
        bail("No directory named %s was found." % options.directory)

    #
    # Execute
    #

    if command == "export":
        action_export(abs_artwork_file_name, abs_directory)
    elif command == "create":
        abs_create_file_name = os.path.abspath(options.create_file_name)
        if os.path.exists(abs_create_file_name):
            bail("Sorry, but the create file %s already exists." % options.create_file_name)
        action_create(abs_artwork_file_name, abs_directory, abs_create_file_name)
            
if __name__ == "__main__":
    main(sys.argv)
    

    
