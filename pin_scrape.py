__author__ = 'sarmar01'
import re
from dwarf_section import *
from pin_scrape import *
import os
import yaml
from elftools.elf.elffile import *


def extract_pins(lines, lineno):
    pins = []
    for i,line in enumerate(lines[lineno:]):
        if ";" in line:
            return pins
        else:
            regex = "{\s*(\w+)\s*,\s*(\w+)\s*,\s*(\w+)\s*}"
            match= re.findall(regex,line)
            if match:
                for m in match:
                    pins.append(m)

def find_pinmaps(filename,linenos):
    with open(filename, "r") as file:
        lines = file.readlines()
        for lineno in linenos:
            regex = r"PinMap PinMap_(\w+)\[\]"
            m = re.search(regex, lines[lineno-1])
            if m:
                type = m.group(1)
                pins = extract_pins(lines,lineno-1)
                yield (type, pins)

def parse_directory_for_pins(target, dirpath, type):
    pin_dict = {}
    files = {}
    for filename in os.listdir(dirpath):
        if ".o" in filename:
            with open(os.path.join(dirpath,filename), "rb") as file:
                elf = ELFFile(file)
                variables = find_variables(elf, type = type)
                for (name, filename, line) in variables:
                    if filename in files:
                        files[filename].append(line)
                    else:
                        files[filename] = [line]

    pin_dict[target] = {}
    for filename in files.keys():
        maps = find_pinmaps(filename, files[filename])
        for type, pins in maps:
            if type in pin_dict[target]:
             pin_dict[target][type].extend(pins)
            else:
                pin_dict[target][type] = pins
    return pin_dict