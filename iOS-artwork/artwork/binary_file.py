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

import mmap

from .util import KnuthMorrisPratt

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
