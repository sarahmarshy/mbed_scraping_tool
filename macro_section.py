""" Parser for gcc specific .debug_macro sections
"""

from elftools.construct import *
from elftools.common.utils import struct_parse

# Struct tags
DEBUG_MACRO_TAGS = dict(
    DW_MACRO_GNU_none                   = 0,
    DW_MACRO_GNU_define                 = 1,
    DW_MACRO_GNU_undef                  = 2,
    DW_MACRO_GNU_start_file             = 3,
    DW_MACRO_GNU_end_file               = 4,
    DW_MACRO_GNU_define_indirect        = 5,
    DW_MACRO_GNU_undef_indirect         = 6,
    DW_MACRO_GNU_transparent_include    = 7,
)

# Debug flags
FLAG_64BIT_DWARF_FORMAT      = 0x1
FLAG_LINEPTR_PRESENT         = 0x2
FLAG_DEPOPCODE_TABLE_PRESENT = 0x4


def create_header_struct(elf, dwarf):
    return Struct('debug_macro_header',
        dwarf.structs.Dwarf_uint16('version'),
        dwarf.structs.Dwarf_uint8('flags'),
        If(lambda ctx: ctx.flags & FLAG_LINEPTR_PRESENT,
            IfThenElse('lineptr', lambda ctx: ctx.flags & FLAG_64BIT_DWARF_FORMAT,
                dwarf.structs.Dwarf_uint64(''),
                dwarf.structs.Dwarf_uint32(''))))

def create_entry_struct(elf, dwarf, flags):
    if flags & FLAG_64BIT_DWARF_FORMAT:
        Macro_addr = dwarf.structs.Dwarf_uint64
    else:
        Macro_addr = dwarf.structs.Dwarf_uint32

    return Struct('debug_macro_entry',
        Enum(dwarf.structs.Dwarf_uint8('tag'), **DEBUG_MACRO_TAGS),
        Switch('value', lambda ctx: ctx.tag, dict(
            DW_MACRO_GNU_none = Embed(Struct('',
            )),
            DW_MACRO_GNU_define = Embed(Struct('',
                dwarf.structs.Dwarf_uleb128('lineno'),
                CString('value'),
            )),
            DW_MACRO_GNU_undef = Embed(Struct('',
                dwarf.structs.Dwarf_uleb128('lineno'),
                CString('value'),
            )),
            DW_MACRO_GNU_start_file = Embed(Struct('',
                dwarf.structs.Dwarf_uleb128('lineno'),
                dwarf.structs.Dwarf_uleb128('fileno'),
            )),
            DW_MACRO_GNU_end_file = Embed(Struct('',
            )),
            DW_MACRO_GNU_define_indirect = Embed(Struct('',
                dwarf.structs.Dwarf_uleb128('lineno'),
                Macro_addr('addr'),
            )),
            DW_MACRO_GNU_undef_indirect = Embed(Struct('',
                dwarf.structs.Dwarf_uleb128('lineno'),
                Macro_addr('addr'),
            )),
            DW_MACRO_GNU_transparent_include = Embed(Struct('',
                Macro_addr('addr'),
            )),
        )))
            

def parse_macro_section(elf, dwarf, section):
    header_struct = create_header_struct(elf, dwarf)

    section.stream.seek(section['sh_offset'])
    header = struct_parse(header_struct, section.stream)
    yield header

    entry_struct = create_entry_struct(elf, dwarf, header.flags)

    while section.stream.tell() - section['sh_offset'] < section['sh_size']:
        yield struct_parse(entry_struct, section.stream)

def parse_macro_sections(elf, dwarf):
    return (parse_macro_section(elf, dwarf, section) 
            for section in elf.iter_sections()
            if section.name == '.debug_macro')
   

def get_macros(elf, dwarf=None):
    dwarf = dwarf or elf.get_dwarf_info(False)

    for section in parse_macro_sections(elf, dwarf):
        header = next(section)

        for entry in section:
            if entry.tag == 'DW_MACRO_GNU_define':
                yield entry.value
            elif entry.tag == 'DW_MACRO_GNU_define_indirect':
                yield dwarf.get_string_from_table(entry.addr)

