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

# generate-from-uikit-binary.py
#
# The code in this file is capable of grabbing the names, sizes, and offsets
# of all images in all (shared) artwork files.
#
# To run it, use:
#
#   ./generate-from-uikit-binary.py /path/to/UIKit /output/path/
#
# In general, you shouldn't have to run this. I'll run it when new versions of the
# OS show up. 
#
# This code works by reading the mach-o header and symbol table from the UIKit
# binary, and then looking for special unexported symbols known to reference
# the names and size/offset information.  To use it, you must have the python
# macholib and PIL installed.

import sys
import struct
import pdb
import os
import mmap
import macholib
from macholib.MachO import MachO
import PIL.Image


#------------------------------------------------------------------------------
# Helpers
#------------------------------------------------------------------------------

def flatten(thing):
    """Take arbitrarily nested lists or tuples and flatten them."""
    if (type(thing) == list) or (type(thing) == tuple):
        for item in thing:
            for flattened in flatten(item):
                yield flattened
    else:
        yield thing
        
        
class KnuthMorrisPratt(object):
    """Implement a search algorithm that works over lists."""
    @staticmethod
    def build_kmp_table(needle):
        m = len(needle)
        pi = [0] * m
        k = 0
        for q in range(1, m):
            while k > 0 and needle[k] != needle[q]:
                k = pi[k - 1]
            if needle[k] == needle[q]:
                k = k + 1
            pi[q] = k
        return pi

    @staticmethod
    def find(needle, haystack, starting_at = 0):
        n = len(haystack)
        m = len(needle)
        pi = KnuthMorrisPratt.build_kmp_table(needle)
        q = 0
        for i in range(starting_at, n):
            while q > 0 and needle[q] != haystack[i]:
                q = pi[q - 1]
            if needle[q] == haystack[i]:
                q = q + 1
            if q == m:
                return i - m + 1
        return -1    


#------------------------------------------------------------------------------
# Binary File
#------------------------------------------------------------------------------

class BinaryFile(object):
    """Represents a binary file on disk, and has tools to rapidly read and search it."""
    def __init__(self, filename):
        super(BinaryFile, self).__init__(filename)
        self.filename = filename
        self._file = None
        self._data = None
        self._data_length = -1
        
    def __del__(self):
        if self._data is not None:
            self._data.close()
            self._data = None
        if self._file is not None:
            self._file.close()
            self._file = None
            
    @property
    def data(self):
        if self._data is None:
            self._file = open(self.filename, "rb")
            self._data = mmap.mmap(self._file.fileno(), 0, access=mmap.ACCESS_READ)
        return self._data
        
    @property
    def data_length(self):
        if self._data_length == -1:
            self._data_length = len(self.data)
        return self._data_length
        
    def find(self, bytes, starting_at = 0):
        return KnuthMorrisPratt.find(bytes, self.data, starting_at)
        
    def find_all(self, bytes):
        """Returns the offsets into the file for all occurences of the 'bytes' sequence"""
        done = False
        occurences = []
        current = 0
        bytes_length = len(bytes)
        while not done:
            occurence = self.find(bytes, starting_at = current)
            done = (occurence == -1)
            if not done:
                occurences.append(occurence)
                current = occurence + bytes_length # Won't find overlaps, but who cares?
        return occurences
        
    def find_all_int(self, the_int):
        bytes = struct.pack('<H', the_int)
        return self.find_all(bytes)
        
    def find_all_ints(self, ints):
        bytes = struct.pack('<%s' % 'H' * len(ints), *ints)
        return self.find_all(bytes)
    
    def find_all_long(self, the_long):
        bytes = struct.pack('<L', the_long)
        return self.find_all(bytes)
        
    def find_all_longs(self, longs):
        bytes = struct.pack('<%s' % 'L' * len(longs), *longs)
        return self.find_all(bytes)
        
        
#------------------------------------------------------------------------------
# Structures
#------------------------------------------------------------------------------
        
class Struct(object):
    pass
    
class CFString(Struct):
    """struct __builtin_CFString { const int *isa; int flags; const char *str; long length; }"""
    SIZE = 16
    
    # See http://www.opensource.apple.com/source/CF/CF-550.42/CFString.c
    kCFHasLengthByte = 0x04
    kCFHasNullByte = 0x08
    kCFIsUnicode = 0x10
    
    def __init__(self, endian, data, offset):
        super(CFString, self).__init__()
        self.endian = endian
        self.data = data
        self.offset = offset
        self.objc_class, self.flags, self.pointer, self.length = struct.unpack_from(("%sLLLL" % endian), data, offset)
        self.is_little_endian = (endian == "<")
        
    @property
    def string(self):
        """Read the const char* (string) portion of a CFString."""
        s = None
        
        if (self.flags & CFString.kCFHasLengthByte):
            assert ord(self.data[self.pointer]) == self.length, "Invalid length or length byte."
            offset += 1
        
        if (self.flags & CFString.kCFIsUnicode):
            bytes = self.data[self.pointer:self.pointer+(self.length * 2)]
            last_byte = self.data[self.pointer+(self.length * 2)]
            if self.is_little_endian:
                s = bytes.decode('utf-16le')
            else:
                s = bytes.decode('utf-16be')
        else:
            bytes = self.data[self.pointer:self.pointer+self.length]
            last_byte = self.data[self.pointer+self.length]
            s = bytes.decode('ascii')
        
        if (self.flags & CFString.kCFHasNullByte):
            assert last_byte == '\0', "Something went wrong reading cfstring."
            
        return s
        
class NList(Struct):
    """struct nlist { int32_t n_un; uint8_t n_type; uint8_t n_sect; int16_t n_desc; uint32_t n_value; }"""
    SIZE = 12
    N_ARM_THUMB_DEF = 0x0008 # See MachOFileAbstraction.hpp
    
    def __init__(self, endian, data, offset):
        super(Struct, self).__init__()
        self.n_strx, self.n_type, self.n_sect, self.n_desc, self.n_value = struct.unpack_from(("%siBBhI" % endian), data, offset)
        
class ArtworkSetInformation(Struct):
    SIZE = 36

    def __init__(self, endian, data, offset):
        super(ArtworkSetInformation, self).__init__()
        # sizes_offset points directly to an array of ArtworkSizeInformation structs
        # names_offset is the address of an array of pointers to cfstrings. (yikes.)
        self.set_name_offset, unk1, unk2, self.sizes_offset, self.names_offset, self.artwork_count, unk3, unk4, unk5, unk6 = struct.unpack_from(("%sLLLLLHHLLL" % endian), data, offset)
        self.endian = endian
        self.data = data
        self.offset = offset
    
    @property
    def name(self):
        return CFString(self.endian, self.data, self.set_name_offset).string
    
    def read_offset(self, offset):
        """Dereference an address found at `offset`"""
        return struct.unpack_from('%sL' % self.endian, self.data, offset)[0]
    
    def iter_artworks(self):
        size_offset = self.sizes_offset
        name_offset = self.names_offset

        # Walk through the artwork and gather information.
        for artwork_i in range(self.artwork_count):
            ai = ArtworkSizeInformation(self.endian, self.data, size_offset)
            name_pointer = self.read_offset(name_offset)
            name_cfstring = CFString(self.endian, self.data, name_pointer)
            
            size_offset += ArtworkSizeInformation.SIZE
            name_offset += 4
            
            yield (name_cfstring.string, ai)
            
    
class ArtworkSizeInformation(Struct):
    """Appears to be struct { unsigned long offset_into_artwork_file; unsigned int width; unsigned int height; }"""
    SIZE = 8
    def __init__(self, endian, data, offset):
        super(ArtworkSizeInformation, self).__init__()
        self.offset, self.width, self.height = struct.unpack_from(("%sLHH" % endian), data, offset)
        
        
#------------------------------------------------------------------------------
# MachOBinaryFile
#------------------------------------------------------------------------------

class MachOBinaryFile(BinaryFile, MachO):
    """Represents a Mach-O binary file, with special methods to 
    find important data in the file."""

    def __init__(self, filename):
        super(MachOBinaryFile, self).__init__(filename)

    @property
    def default_header(self):
        return self.headers[0]
        
    @property
    def default_endian(self):
        return self.default_header.endian
        
    @property
    def is_little_endian(self):
        return self.default_endian == "<"
        
    @property
    def is_big_endian(self):
        return self.default_endian == ">"

    @property
    def default_header_offset(self):
        # TODO: this is an assumption which probably doesn't hold true everywhere? What about fat headers?
        return 0

    def macho_sections(self):
        for flat in flatten(self.default_header.commands):
            if type(flat) == macholib.mach_o.section:
                yield flat
                
    def macho_section(self, sectname, segname):
        for section in self.macho_sections():
            if section.sectname.startswith(sectname) and section.segname.startswith(segname):
                return section
        return None
        
    def cfstring_section(self):
        return self.macho_section('__cfstring', '__DATA')
        
    def iter_cfstrings(self):
        cfs = self.cfstring_section()
        string_count = cfs.size / CFString.SIZE
        for i in range(string_count):
            cfstring_addr = cfs.addr + (i * CFString.SIZE)
            cfstring = self.read_cfstring(cfstring_addr)
            yield cfstring
            
    def iter_strings(self):
        for cfstring in self.iter_cfstrings():
            yield cfstring.string

    def read_cfstring(self, offset):
        """Read a constant CFString structure from the binary."""
        return CFString(self.default_endian, self.data, offset)
        
    def read_nlist(self, offset):
        """Read an nlist entry from the binary."""
        return NList(self.default_endian, self.data, offset)
        
    def read_cstring(self, offset):
        """Read an ASCII null-terminated C String from the binary."""
        end = offset
        while self.data[end] != '\0':
            end += 1
        return self.data[offset:end].decode('ascii')
        
    def read_offset(self, offset):
        """Read a pointer value found at given offset."""
        return struct.unpack_from('%sL' % self.default_endian, self.data, offset)

    def find_symbol(self, symbol):
        """Given a symbol (potentially not exported), return the offset into the binary where
        that symbol's data is found."""
        
        #
        # Find the relevant segments and symbol table.
        #
        segment_linkedit = None
        segment_text = None
        symbol_table = None
        
        for load_command, segment_command, data in self.default_header.commands:
            if load_command.cmd == macholib.mach_o.LC_SEGMENT:
                if segment_command.segname.startswith(macholib.mach_o.SEG_TEXT):
                    segment_text = segment_command
                elif segment_command.segname.startswith(macholib.mach_o.SEG_LINKEDIT):
                    segment_linkedit = segment_command
            elif load_command.cmd == macholib.mach_o.LC_SYMTAB:
                symbol_table = segment_command # effectively a cast...
        
        if (segment_linkedit is None) or (segment_text is None) or (symbol_table is None):
            return None
        
        #
        # Compute key offsets into the file
        #
        
        vm_slide = self.default_header_offset - segment_text.vmaddr
        symbols_addr = self.default_header_offset + symbol_table.symoff
        strings_addr = self.default_header_offset + symbol_table.stroff
        
        symbol_addr = symbols_addr
        for i in range(symbol_table.nsyms):
            symbol_nlist = NList(self.default_endian, self.data, symbol_addr)
            string_addr = strings_addr + symbol_nlist.n_strx
            read_symbol = self.read_cstring(string_addr)
            if (symbol_nlist.n_strx != 0) and (symbol == read_symbol):
                address = vm_slide + symbol_nlist.n_value
                if (symbol_nlist.n_desc & NList.N_ARM_THUMB_DEF) != 0:
                    return (address | 1)
                else:
                    return address
            symbol_addr += NList.SIZE
        
        return None


#------------------------------------------------------------------------------
# UIKitBinaryFile
#------------------------------------------------------------------------------

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
    
        
#------------------------------------------------------------------------------
# ArtworkBinaryFile
#------------------------------------------------------------------------------

class ArtworkBinaryFile(BinaryFile):
    """Represents an iPhone SDK .artwork file"""
    def __init__(self, filename):
        super(ArtworkBinaryFile, self).__init__(filename)


#------------------------------------------------------------------------------
# main()
#------------------------------------------------------------------------------

def main():
    uikit = UIKitBinaryFile(sys.argv[1])
    
    for artwork_set in uikit.iter_shared_iphone_image_sets():
        print "Found artwork set named %s" % artwork_set.name
        for artwork_name, artwork_size in artwork_set.iter_artworks():
            print "\t%s: (%d x %d at %X)" % (artwork_name, artwork_size.width, artwork_size.height, artwork_size.offset)

    for artwork_set in uikit.iter_shared_ipad_image_sets():
        print "Found artwork set named %s" % artwork_set.name
        for artwork_name, artwork_size in artwork_set.iter_artworks():
            print "\t%s: (%d x %d at %X)" % (artwork_name, artwork_size.width, artwork_size.height, artwork_size.offset)
    
    
if __name__ == "__main__":
    main()


# Random useless notes
# For Shared~iphone.artwork, 4256480 (0x0040F2E0)
# next is at 4256495 (0x0040F2EF)
# Name indexes start at 5497296 (0x0053E1D0) -- really 0x0053e1c8 is the start of the NSConstantString
# Indirect name indexes start at one of {5407456, 5410496, 5415136, 5497288}
# looks like 4 bytes index, 2 bytes for length, 2 bytes unknown, 4 bytes unknown, 4 bytes often C8070000
