import json
import os
import subprocess
import base64
import urllib3

from utils import *


def handler(event):
    print("[+] LaRE is starting")

    try:
        action, data = parse_event(event.get_json())
        if action == CMD_OP:
            result, output = run_cmd(data)
            if result == 0:
                result = Status.OK
            else:
                result = Status.ERR
            output = base64.b64encode(output).decode("utf-8")

        elif action == SPECIAL_OP:
            result, output = run_special(data)
            if result == 0:
                result = Status.OK
            else:
                result = Status.ERR
            output = base64.b64encode(output).decode("utf-8")

        elif action == GET_FILE_OP:
            result, output = run_getfile(data)
            output = output.decode("utf-8")

        elif action == PUT_FILE_OP:
            result, output = run_putfile(data)
            output = base64.b64encode(output.encode("utf-8")).decode("utf-8")

        return construct_response(result, output)
    except Exception as err:
        return construct_response(Status.EXCEPTION, base64.b64encode(str(err).encode("utf-8")).decode("utf-8"))


def parse_event(event):
    if "body" in event:
        body = json.loads(event["body"])
    else:
        body = event

    if OP in body and ARGS in body:
        if body[OP] == CMD_OP:
            action = CMD_OP
        elif body[OP] == GET_FILE_OP:
            action = GET_FILE_OP
        elif body[OP] == PUT_FILE_OP:
            action = PUT_FILE_OP
        elif body[OP] == SPECIAL_OP:
            action = SPECIAL_OP
        else:
            raise Exception(f"[!] parse_event - Unknown operation {body[OP]}")
        return action, body[ARGS]
    else:
        raise Exception(f"[!] parse_event - Lack of operation and / or args {body}")


def run_cmd(cmd):
    os.environ['PYTHONUNBUFFERED'] = "1"
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    output, _ = proc.communicate()
    rc = proc.returncode
    return rc, output


def run_special(cmd):
    if cmd.startswith("curl"):
        return curl(cmd) 


def curl(cmd):
    try:
        addr = cmd.split(" ")[1]
        http = urllib3.PoolManager()
        response = http.request("GET", addr, timeout=1.5, retries=False)
    except Exception as err:
        raise Exception(f"[!] curl - Some error when using urllib3: {repr(err)}")
    return Status.OK, response.data


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
    mode = read_to_write[args["mode"]]
    is_compressed = args["is_compressed"]

    if mode == "w":
        decoded = decoded.decode("utf-8")
    
    try:
        writefile(path, mode, decoded)
    except IOError as err:
        raise Exception(f"[!] run_putfile - file {path} failed with IOError: {repr(err)}")

    if is_compressed:
        try:
            extract_bz2(path, path[:4])
        except Exception as err:
            raise Exception(f"[!] run_putfile - something went wrong during decompression: {repr(err)}\nCompressed file was saved: {path}")
        return Status.OK, f"File successfully saved: {path}\nFile successfully decompressed: {path[:4]}"

    return Status.OK, f"File successfully saved: {path}"


def construct_response(result, output):
    response = json.dumps({
            "result": result.value,
            "output": output
        })
    
    return response