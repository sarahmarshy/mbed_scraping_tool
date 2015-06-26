#!/usr/bin/env python

import sys
import re
import os
from elftools.elf.elffile import ELFFile
import macro_section
from itertools import chain

def find_enums(dwarfinfo):
    for CU in dwarfinfo.iter_CUs():
        for DIE in CU.iter_DIEs():
            if DIE.tag == 'DW_TAG_enumerator':
                yield (DIE.attributes['DW_AT_name'].value,
                       int(DIE.attributes['DW_AT_const_value'].value))

def find_macros(elf, dwarfinfo):
    macros = macro_section.get_macros(elf,dwarfinfo)

    for string in macros:
        #if string:
            match = re.match('^(?!_)(\w+) (.+)$', string)
            if 'FTM_CnSC_REG' in string:
                print "HERE"
            if match:
                yield (match.group(1),(match.group(2)))

def replace_references(d,v):
    try:
        v = re.sub(r'(\b[0-9A-Fa-fxX]+)[uUlLfF]+',r'\1',v)
        return eval(v)
    except (NameError,),e:
        undefined = re.findall("name '(\w+)' is not defined",str(e))
        for u in undefined:
            v = v.replace(u, str(d[u]))
            return replace_references(d, v)

def find_defines_in_file(filename):
    print filename
    with open(filename, 'rb') as file:
        elffile = ELFFile(file)
        assert elffile.has_dwarf_info()

        dwarfinfo = elffile.get_dwarf_info(False)
        for enum in find_enums(dwarfinfo):
            yield enum
        for macro in find_macros(elffile, dwarfinfo):
            yield macro

def find_defines(*filenames):
    defines = chain.from_iterable(find_defines_in_file(filename) for filename in filenames)
    d = dict(defines)
    for k,v in d.items():
        d[k] = replace_references(d,v)
    return d


print find_defines(*[os.path.join("C:\\Users\\sarmar01\\Documents\\obj_files",f) for f in os.listdir("C:\\Users\\sarmar01\\Documents\\obj_files")])
