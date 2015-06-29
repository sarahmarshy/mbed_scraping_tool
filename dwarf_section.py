#!/usr/bin/env python

import re
from os import path
from itertools import chain
from macro_section import find_macros


def find_enums(elf, dwarf=None):
    dwarf = dwarf or elf.get_dwarf_info(False)

    for cu in dwarf.iter_CUs():
        for die in cu.iter_DIEs():
            if die.tag == 'DW_TAG_enumerator':
                yield (die.attributes['DW_AT_name'].value, 
                       die.attributes['DW_AT_const_value'].value)

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

def variable_types(cu, die):
    while 'DW_AT_type' in die.attributes:
        die = type(die)(cu, die.stream, die.attributes['DW_AT_type'].value)

        if 'DW_AT_name' in die.attributes:
            yield die.attributes['DW_AT_name'].value

def find_types(elf, dwarf=None, type=None):
    dwarf = dwarf or elf.get_dwarf_info(False)
    types = set()

    for cu in dwarf.iter_CUs():
        for die in cu.iter_DIEs():
            if die.tag == 'DW_TAG_variable':
                for type in variable_types(cu, die):
                    types.add(type)

    return types

def find_variables(elf, dwarf=None, type=None):
    dwarf = dwarf or elf.get_dwarf_info(False)

    for cu in dwarf.iter_CUs():
        for die in cu.iter_DIEs():
            if (die.tag == 'DW_TAG_variable' and
                'DW_AT_decl_line' in die.attributes and
                'DW_AT_decl_file' in die.attributes):
                for attr in 'DW_AT_name', 'DW_AT_linkage_name':
                    if attr in die.attributes:
                        name = die.attributes[attr].value
                        break
                else:
                    assert False, "No name found!"

                line_program = dwarf.line_program_for_CU(cu)
                file_entry = line_program['file_entry'][
                        die.attributes['DW_AT_decl_file'].value-1]
                dir_entry = line_program['include_directory'][
                        file_entry.dir_index-1]
                file = path.join(dir_entry, file_entry.name)

                if not type or any(t == type for t in variable_types(cu, die)):
                    yield (name, file, die.attributes['DW_AT_decl_line'].value)

if __name__=="__main__":
    from elftools.elf.elffile import ELFFile
    import sys

    with open(sys.argv[1], 'rb') as file:
        elf = ELFFile(file)

        print "Constants:"
        for k, v in find_constants(elf):
            print '%s = %s' % (k, v)
        print

        print "Types:"
        for k in find_types(elf):
            print k
        print

        print "Variables:"
        for k, f, l in find_variables(elf):
            print '%s = %s:%s' %  (k, f, l)
        print
