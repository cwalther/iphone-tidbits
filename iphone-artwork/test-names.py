#!/usr/bin/env python

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
# MachOBinaryFile
#------------------------------------------------------------------------------
        
class MachOBinaryFile(BinaryFile, MachO):
    """Represents a Mach-O binary file, with special methods to 
    find important data in the file."""

    # How large is the NSConstantString struct, in bytes?
    NSCONSTANTSTRING_SIZE = 16
    
    def __init__(self, filename):
        super(MachOBinaryFile, self).__init__(filename)

    @property
    def default_header(self):
        return self.headers[0]
        
    @property
    def default_endian(self):
        return self.default_header.endian

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
        
    def iter_strings(self):
        cfs = self.cfstring_section()
        string_count = cfs.size / MachOBinaryFile.NSCONSTANTSTRING_SIZE
        for i in range(string_count):
            cfstring_addr = cfs.addr + (i * MachOBinaryFile.NSCONSTANTSTRING_SIZE)
            pointer, length = self.read_cfstring(cfstring_addr)
            yield (cfstring_addr, pointer, length, self.read_string(pointer, length))

    def read_cfstring(self, offset):
        # NSConstantString { Class class; char *string; int length }
        objc_class, pointer, length = struct.unpack_from('<QLL', self.data, offset)
        return (pointer, length)

    def read_string(self, offset, length):
        # TODO encoding: which to use?
        bytes = self.data[offset:offset+length]
        # assert self.data[offset+length] == '\0', "Didn't read proper length."
        return bytes.decode('mac-roman')


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

def find_png_strings(library):
    for cfstring_addr, pointer, length, string in library.iter_strings():
        if string.endswith('.png'):
            found_refs = library.find_all_long(cfstring_addr)
            print '[%X] %r %s' % (cfstring_addr, string, found_refs)
    
def main():
    library = MachOBinaryFile(sys.argv[1])
    find_png_strings(library)
        
if __name__ == "__main__":
    main()

# 
# def read_string(data, offset):
#     string = ''
#     while data[offset] != '\0':
#         string += data[offset]
#         offset += 1
#     return string
#     
# def read_ns_constant_string(data, offset):
#     # 
#     objc_class, char_star, length = struct.unpack_from('<QL', data, offset)
#     return char_star
#     
# f = open(sys.argv[1])
# binary = f.read()
# f.close()
# 
# indirect = int(sys.argv[2])
# count = int(sys.argv[3])
# 
# i = 0
# while i < count:
#     binary_string_table_offset = struct.unpack_from('<L', data, indirect)[0]
#     binary_offset = read_binary_offset(binary, binary_string_table_offset)
#     binary_string_table_offset += 16
#     s = read_string(binary, binary_offset)
#     assert len(s) > 0, "Whoops"
#     print '[%d] %s' % (i, s)
#     i += 1

# For Shared~iphone.artwork, 4256480 (0x0040F2E0)
# next is at 4256495 (0x0040F2EF)
# Name indexes start at 5497296 (0x0053E1D0) -- really 0x0053e1c8 is the start of the NSConstantString
# Indirect name indexes start at one of {5407456, 5410496, 5415136, 5497288}
# looks like 4 bytes index, 2 bytes for length, 2 bytes unknown, 4 bytes unknown, 4 bytes often C8070000
