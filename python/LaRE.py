import json
import os
import subprocess
import base64

from enum import Enum
from .utils import *


def handler(event, context):
    print("[+] LaRE is starting")

    try:
        action, data = parse_event(event)

        if action == CMD_OP:
            status, output = run_cmd(data)
            resp_type = ResponseType.CMD

        elif action == GET_FILE_OP:
            status, output = run_getfile(data)
            resp_type = ResponseType.GETFILE

        elif action == PUT_FILE_OP:
            status, output = run_putfile(data)
            resp_type = ResponseType.PUTFILE

        return construct_response(resp_type, status, output)
    except Exception as err:
        return construct_response(ResponseType.ERR, Status.EXCEPTION, err)


def parse_event(event):
    if "body" in event:
        body = json.loads(event["body"])
    else:
        body = event

    if OP and ARGS in body:
        if body[OP] == CMD_OP:
            action = CMD_OP
        elif body[OP] == GET_FILE_OP:
            action = GET_FILE_OP
        elif body[OP] == PUT_FILE_OP:
            action = PUT_FILE_OP
        else:
            raise Exception(f"[!] parse_event - Unknown operation {body[ACTION]}")
        return action, body[ARGS]
    else:
        raise Exception(f"[!] parse_event - Lack of operation and / or args f{body}")


def run_cmd(cmd):
    os.environ['PYTHONUNBUFFERED'] = True
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    output, _ = proc.communicate()
    rc = proc.returncode
    return rc, output


def run_getfile(path):
    if not os.path.exists(path):
        return Status.ERR, f"[-] run_getfile - file {path} doesn't exist on Lambda"

    try:
        mode = check_type(path)
        status_type = Status.OK_BIN
        content = readfile(path, mode)

        if mode == "r":
            content = content.encode("utf-8")
            status_type = Status.OK
        encoded = base64.b64encode(content)

        if len(encoded) < MAX_BODY_SIZE:
            return status_type, encoded

        content_len = len(content)
        encoded_len = len(encoded)
        del content, encoded

        bz2_path = get_bz2_path(path)
        create_compressed_file(path, bz2_path)

        content = readfile(bz2_path, "rb")
        os.unlink(bz2_path)

        encoded = base64.b64encode(content)
        if len(encoded) < MAX_BODY_SIZE:
            return Status.OK_BZ2, encoded

    except UnicodeDecodeError:
        raise Exception(f"[!] run_getfile - file {path} failed with UnicodeDecodeError")
    except IOError as err:
        raise Exception(f"[!] run_getfile - file {path} failed with IOError: {repr(err)}")
    raise Exception(f"[-] run_getfile - file {path} too big - Size: {content_len} | Encoded size: {encoded_len} | Compressed size: {len(content)} | Encoded compressed size: {len(encoded)}")
    

def run_putfile(args):
    path = args["path"]
    decoded = base64.b64decode(args["content"].encode("utf-8"))
    mode = args["mode"]
    is_compressed = args["is_compressed"]

    # TODO rest of function


def construct_response(resp_type, status, output):
    if resp_type == ResponseType.CMD:
        output = base64.b64encode(output).decode("utf-8")
    elif resp_type == ResponseType.GETFILE:
        continue
    elif resp_type == ResponseType.PUTFILE:
        pass
    elif resp_type == ResponseType.ERR:
        output = base64.b64encode(output.encode("utf-8")).decode("utf-8")
    response = {
        "statusCode": 200,
        "headers" {
            "Content-Type": "application/json"
        }
        "body": json.dumps({
            "status": status.value,
            "output": output
        })
    }
    return response