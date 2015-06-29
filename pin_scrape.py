__author__ = 'sarmar01'
import re

def extract_pins(lines, lineno):
    for i,line in enumerate(lines[lineno:]):
        if ";" in line:
            return
        else:
            regex = "\s*{(\w+)\s*,\s*(\w+)\s*,\s*(\d+)}\s*,"
            m = re.search(regex,line)
            if m:
                yield (m.group(1),m.group(2),m.group(3))

def find_pinmaps(filename,linenos):
    print filename
    with open(filename, "r") as file:
        lines = file.readlines()
        for lineno in linenos:
            print lineno
            regex = r"PinMap PinMap_(\w+)\[\]"
            m = re.search(regex, lines[lineno-1])
            if m:
                type = m.group(1)
                yield (type, extract_pins(lines,lineno-1))


