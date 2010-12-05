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

import macholib                     # You must have macholib installed. Search PyPi for it!
from macholib.MachO import MachO

from .binary_file import BinaryFile
from .structs import NList

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
        # Compute key offsets into the file. 
        #
        
        # (The file wasn't loaded via dyld so we don't have to compute vm/file slides.)
        symbols_addr = self.default_header_offset + symbol_table.symoff
        strings_addr = self.default_header_offset + symbol_table.stroff
        
        symbol_addr = symbols_addr
        for i in range(symbol_table.nsyms):
            symbol_nlist = NList(self.default_endian, self.data, symbol_addr)
            string_addr = strings_addr + symbol_nlist.n_strx
            read_symbol = self.read_cstring(string_addr)
            if (symbol_nlist.n_strx != 0) and (symbol == read_symbol):
                address = symbol_nlist.n_value
                if (symbol_nlist.n_desc & NList.N_ARM_THUMB_DEF) != 0:
                    return (address | 1)
                else:
                    return address
            symbol_addr += NList.SIZE
        
        return None
