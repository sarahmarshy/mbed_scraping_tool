__author__ = 'sarmar01'
from macro_section import get_macros
from elftools.elf.elffile import ELFFile
import re
import os
import sys


def create_file(filename, output_filename=None):
     output_filename = output_filename or new_extension(filename, "c")

     with open(filename, 'rb') as file:
        elffile = ELFFile(file)
        macros = list(get_macros(elffile))

        with open(output_filename, 'w') as c_file:
            # for m in macros:
            #     if not re.match("__",m):
            #         c_file.write('#define %s\n' % m)

            for m in macros:
                match = re.match("(?!__)(\w+) .+", m)
                if match:
                    #c_file.write('enum { %s__enum = (unsigned int)(%s) };\n'% (match.group(1), match.group(1)))
                    c_file.write('const unsigned int %s__const = (unsigned int)(%s);\n'% (match.group(1), match.group(1)))


def new_extension(filename, ext):
        new_name = filename.split('.')
        return ".".join((new_name[0], 'enum', ext))


if __name__ ==  "__main__":
    create_file(sys.argv[1], sys.argv[2] if len(sys.argv) > 1 else None)