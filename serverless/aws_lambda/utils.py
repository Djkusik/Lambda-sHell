import tarfile
import os

from enum import Enum

class Status(Enum):
    OK = 1
    ERR = 2
    EXCEPTION = 3
    OK_BIN = 4
    OK_BZ2 = 5


class ResponseType(Enum):
    CMD = 1
    GETFILE = 2
    PUTFILE = 3
    ERR = 4


OP = "action"
CMD_OP = "cmd"
SPECIAL_OP = "special"
GET_FILE_OP = "getfile"
PUT_FILE_OP = "putfile"
ARGS = "args"
MAX_PAYLOAD_SIZE = 6291456
MAX_BODY_SIZE = MAX_PAYLOAD_SIZE - 500
SPECIAL_CMDS = ("curl")

read_to_write = {
    "r": "w",
    "rb": "wb"
}


textchars = bytearray({7,8,9,10,12,13,27} | set(range(0x20, 0x100)) - {0x7f})
is_binary_string = lambda bytes: bool(bytes.translate(None, textchars))
get_bz2_path = lambda path: "/tmp/" + os.path.basename(path) + ".bz2"


def check_type(path):
    with open(path, "rb") as file:
        if is_binary_string(file.read(1024)):
            return "rb"
        else:
            return "r"


def readfile(path, mode):
    with open(path, mode) as file:
        return file.read()


def writefile(path, mode, data):
    with open(path, mode) as file:
        file.write(data)


def create_compressed_file(in_path, out_path):
    with tarfile.open(out_path, "w:bz2") as bz2:
        bz2.add(in_path, arcname=os.path.basename(in_path))


def extract_bz2(in_path, out_path):
    with tarfile.open(in_path, "r:bz2") as bz2:
        bz2.extractall(path=out_path)