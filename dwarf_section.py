#!/usr/bin/env python

import re
from itertools import chain
from macro_section import find_macros


def find_enums(elf, dwarf=None):
    dwarf = dwarf or elf.get_dwarf_info(False)

    for CU in dwarf.iter_CUs():
        for DIE in CU.iter_DIEs():
            if DIE.tag == 'DW_TAG_enumerator':
                yield (DIE.attributes['DW_AT_name'].value, 
                       DIE.attributes['DW_AT_const_value'].value)

def replace_references(d, v):
    try:
        v = re.sub(r'(\b[0-9A-Fa-fxX]+)[uUlLfF]+',r'\1',v)
        return eval(v)
    except (NameError,),e:
        undefined = re.findall("name '(\w+)' is not defined",str(e))
        for u in undefined:
            v = v.replace(u, str(d[u]))
        return replace_references(d, v)

def find_defines(elf, dwarf=None):
    macros = find_macros(elf, dwarf)
    mapping = {}

    for string in macros:
        match = re.match(r'^(?!__)(\w+) (.+)$', string)
        if match:
            mapping[match.group(1)] = match.group(2)

    for k, v in mapping.iteritems():
        try:
            mapping[k] = replace_references(mapping, v)
        except:
            del mapping[k]

    return mapping.iteritems()

def find_constants(elf, dwarf=None):
    dwarf = dwarf or elf.get_dwarf_info(False)

    return chain(find_defines(elf, dwarf),
                 find_enums(elf, dwarf))

def find_variables(elf, dwarf=None):
    dwarf = dwarf or elf.get_dwarf_info(False)

    for CU in dwarf.iter_CUs():
        for DIE in CU.iter_DIEs():
            if DIE.tag == 'DW_TAG_variable':
                compile_unit = CU.get_top_DIE()
                assert compile_unit.tag == 'DW_TAG_compile_unit'

                yield (DIE.attributes['DW_AT_name'].value, 
                       compile_unit.get_full_path(),
                       DIE.attributes['DW_AT_decl_line'].value)

if __name__=="__main__":
    from elftools.elf.elffile import ELFFile
    import sys

    with open(sys.argv[1], 'rb') as file:
        elf = ELFFile(file)

        for k, v in find_constants(elf):
            print '%s = %s' % (k, v)

        for k, f, l in find_variables(elf):
            print '%s = %s:%s' %  (k, f, l)
