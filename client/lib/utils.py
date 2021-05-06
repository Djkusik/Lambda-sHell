import argparse
import sys

from enum import Enum


class Status(Enum):
    OK = 1
    ERR = 2
    EXCEPTION = 3


class FSState(Enum):
    NEW_FS_CONT = 1
    NEW_FS_STOP = 2
    SAME_FS = 3
    EXCEPTION_FS = 4


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('addr', help='Lambda address', type=str)
    parser.add_argument('-fs', help='Filesystem tracking', action='store_true')
    args = parser.parse_args()

    if not args.addr:
        print("#TODO USAGE")
        sys.exit(2)
    
    return args.addr, args.fs