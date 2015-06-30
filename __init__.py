__author__ = 'sarmar01'
import os
import subprocess
from workspace_tools.targets import TARGETS, TARGET_MAP, TARGET_NAMES
from workspace_tools.toolchains import TOOLCHAIN_CLASSES
import shutil
import tempfile
from pin_scrape import *
from multiprocessing import Pool
import yaml


path = os.path.realpath(os.path.relpath("..\\..\\..\\mbed", __file__))
text_files_dir = os.path.join(path,"Pins")

def find_pins():
    if not os.path.exists(text_files_dir):
        os.mkdir(text_files_dir)

    build_script = os.path.join(path,"workspace_tools","build.py")
    toolchain = "GCC_ARM"

    command = ["python", build_script, "-t", toolchain, "-o","debug-info", "-j", "0"]
    subprocess.call(command)

    pool = Pool(processes=4)
    pool.map(call_commands, TARGETS)

def call_commands(target):
    print "Finding pins for : " + target.name

    toolchain = "GCC_ARM"
    toolchain_path = "TOOLCHAIN_" + str(TOOLCHAIN_CLASSES[toolchain].__name__)
    build_path = os.path.join(path,"build","mbed","TARGET_"+target.name, toolchain_path)

    try:
        os.chdir(build_path)
    except:
        return

    debug_path = os.path.join(build_path,"debug_files")
    if not os.path.exists(debug_path):
        os.mkdir(debug_path)

    file = "libmbed.a"
    if not os.path.exists(os.path.join(build_path,file)):
        return
    if not os.path.exists(os.path.join(debug_path,file)):
        os.rename(os.path.join(build_path,file),os.path.join(debug_path,file))

    os.chdir(debug_path)
    command = ["arm-none-eabi-ar","x",file]
    subprocess.call(command)

    y = yaml.safe_dump(parse_directory_for_pins(target.name, debug_path, "PinMap"))

    filename = target.name + ".txt"
    file_path = os.path.join(text_files_dir,filename)
    output = open(file_path, 'w')
    output.write(y)
    output.close()

    return


if __name__ == "__main__":
    find_pins()