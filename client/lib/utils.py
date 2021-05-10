import argparse
import sys

from enum import Enum


class Status(Enum):
    OK = 1
    ERR = 2
    EXCEPTION = 3
    OK_BIN = 4
    OK_ZIP = 5


class FSState(Enum):
    NEW_FS_CONT = 1
    NEW_FS_STOP = 2
    SAME_FS = 3
    EXCEPTION_FS = 4


textchars = bytearray({7,8,9,10,12,13,27} | set(range(0x20, 0x100)) - {0x7f})
is_binary_string = lambda bytes: bool(bytes.translate(None, textchars))


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('addr', help='Lambda address', type=str)
    parser.add_argument('-fs', help='Filesystem tracking', action='store_true')
    args = parser.parse_args()

    if not args.addr:
        print("#TODO USAGE")
        sys.exit(2)
    
    return args.addr, args.fs


def writefile(path, mode, data):
    with open(path, mode) as f:
        f.write(data)


def readfile(path, mode):
    with open(path, mode) as f:
        return f.read()