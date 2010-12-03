#!/usr/bin/env python

import sys
import struct
import pdb
import os
import mmap
import PIL.Image

WIDTH_BYTE_ALIGNMENT = 8
TOO_BIG_SIZE = 1024

def align_bytes(byte_location, alignment_amount):
    remainder = byte_location % alignment_amount
    if remainder != 0:
        byte_location += (alignment_amount - remainder)
    return byte_location

def byte_offset(x, y, memory_width):
    return (4 * ((y * memory_width) + x))

def action_search(framework_binary, wh_pairs, debug = True):
    print "Searching for image sizes, starting with ", wh_pairs
    wh_bytes = []
    for wh_pair in wh_pairs:
        w, h = wh_pair
        desired_offset = 0
        wh_bytes.append(struct.pack('<LHH', desired_offset, w, h))

    # f = open(framework_binary, "rb")
    data = framework_binary # mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)

    skip_bytes = len(wh_bytes) * 8
    guess_offset = 0
    matches = []

    while (guess_offset+skip_bytes) < len(data):    
        found = False
        while not found and (guess_offset + skip_bytes) < len(data):
            temp_offset = 0
            for i in range(len(wh_bytes)):
                wh_byte = wh_bytes[i]
                if wh_byte != data[guess_offset+temp_offset:guess_offset+temp_offset+len(wh_byte)]:
                    break
                temp_offset += skip_bytes
                if i == len(wh_bytes) - 1:
                    found = True
            if not found:
                guess_offset += 1
        if found:
            matches.append(guess_offset)
            guess_offset += skip_bytes

    if debug:
        if len(matches) > 0:            
            print "Found likely matches:"
            for match in matches:
                print "\t0x%X (%d)" % (match, match)
        else:
            print "Sorry, no match was found."

    # data.close()
    # f.close()
    return matches


# Read the binary
f = open(sys.argv[1])
binary = f.read()
f.close()


# Read the artwork file
f = open(sys.argv[2])
artwork = f.read()
f.close()

# Compute potential offsets...
potential_offsets = action_search(binary, [(int(sys.argv[4]), int(sys.argv[5]))], debug = False)
print "Found %d potential offsets." % len(potential_offsets)

# Figure out image sizes until we run out...
for potential_offset in potential_offsets:
    print "Working on potential offset 0x%X (%d)" % (potential_offset, potential_offset)
    
    binary_offset = potential_offset
    image_infos = []
    done = False
    first = True

    while not done:
        artwork_offset, w, h = struct.unpack_from("<LHH", binary, binary_offset)
        done = (artwork_offset >= len(artwork)) or ((artwork_offset == 0) and not first)
        first = False
        if not done:
            binary_offset += 8
            image_infos.append((artwork_offset, w, h))

    # Export the images...
    export_directory = os.path.join(sys.argv[3], 'offset-%d' % potential_offset)

    try:
        os.makedirs(export_directory)
    except:
        pass

    print "\t...found %d images at offset 0x%X (%d)" % (len(image_infos), potential_offset, potential_offset)

    for i, (artwork_offset, width, height) in enumerate(image_infos):
        exported_image = PIL.Image.new("RGBA", (width, height))
        exported_pixels = exported_image.load()

        memory_width = align_bytes(width, WIDTH_BYTE_ALIGNMENT)
        
        if (width > TOO_BIG_SIZE) or (height > TOO_BIG_SIZE):
            print "\t\t...abandoned because an image was too big: (%d x %d) (0x%X // %d)" % (width, height, artwork_offset, artwork_offset)
            rmdir
            break
        elif byte_offset(width - 1, height - 1, memory_width) + artwork_offset >= len(artwork):
            print "\t\t...abandoned because an image walked over the artwork byte boundary."
            break
        else:
            for y in range(height):
                for x in range(width):
                    pixel_position = artwork_offset + byte_offset(x, y, memory_width)
                    b, g, r, a = struct.unpack_from('<BBBB', artwork, pixel_position)
                    exported_pixels[x, y] = (r, g, b, a)
        
            image_name = os.path.join(export_directory, 'test-%d.png' % i)
            exported_image.save(image_name, "PNG")
            # print "Exported %s" % image_name


# 6031328 -- some strings of interest
# two bytes before give: 12488, 12495, 12502, 12509, 12516, et. al
# 0x484720
# REALLY IMPORTANT OFFSET 4256479 or 4256480
