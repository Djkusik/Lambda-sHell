import argparse
import sys
import tarfile
import os

from enum import Enum


class Status(Enum):
    OK = 1
    ERR = 2
    EXCEPTION = 3
    OK_BIN = 4
    OK_BZ2 = 5


class FSState(Enum):
    NEW_FS_CONT = 1
    NEW_FS_STOP = 2
    SAME_FS = 3
    EXCEPTION_FS = 4


textchars = bytearray({7,8,9,10,12,13,27} | set(range(0x20, 0x100)) - {0x7f})
is_binary_string = lambda bytes: bool(bytes.translate(None, textchars))
get_bz2_path = lambda path: "./" + os.path.basename(path) + ".bz2"


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('addr', help='Lambda address', type=str)
    parser.add_argument('-fs', help='Filesystem tracking', action='store_true')
    args = parser.parse_args()

    if not args.addr:
        print("#TODO USAGE")
        sys.exit(2)
    
    return args.addr, args.fs


def check_type(path):
    with open(path, "rb") as file:
        if is_binary_string(file.read(1024)):
            return "rb"
        else:
            return "r"


def writefile(path, mode, data):
    with open(path, mode) as file:
        file.write(data)


def readfile(path, mode):
    with open(path, mode) as file:
        return file.read()


def create_compressed_file(in_path, out_path):
    with tarfile.open(out_path, "w:bz2") as bz2:
        bz2.add(in_path, arcname=os.path.basename(in_path))


def extract_bz2(in_path, out_path):
    with tarfile.open(in_path, "r:bz2") as bz2:
        def is_within_directory(directory, target):
            
            abs_directory = os.path.abspath(directory)
            abs_target = os.path.abspath(target)
        
            prefix = os.path.commonprefix([abs_directory, abs_target])
            
            return prefix == abs_directory
        
        def safe_extract(tar, path=".", members=None, *, numeric_owner=False):
        
            for member in tar.getmembers():
                member_path = os.path.join(path, member.name)
                if not is_within_directory(path, member_path):
                    raise Exception("Attempted Path Traversal in Tar File")
        
            tar.extractall(path, members, numeric_owner=numeric_owner) 
            
        
        safe_extract(bz2, path=out_path)