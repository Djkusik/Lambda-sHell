import json
import os
import subprocess

from enum import Enum


class Status(Enum):
    OK = 1
    ERR = 2
    EXCEPTION = 3

OP = "action"
CMD_OP = "cmd"
ARGS = "args"


def handler(event, context):
    print("[+] LaRE is starting")

    try:
        action, data = parse_event(event)

        if action == CMD_OP:
            status, output = run_cmd(data)
    except Exception as err:
        return construct_response("error", Status.EXCEPTION, err)


def parse_event(event):
    if "body" in event:
        body = json.loads(event["body"])
    else:
        body = event

    if OP and ARGS in body:
        if body[OP] == CMD_OP:
            action = CMD_OP
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


def construct_response(type, status, output):
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