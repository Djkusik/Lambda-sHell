import requests
import json
import sys
import os
import base64

from termcolor import colored
from .message import Messages
from .exceptions import *
from .utils import *

class PseudoShell:

    messages = Messages()
    FS_TRACKER_PATH = "/tmp/.sHell_tracker"
    EXIT_CMDS = ("q", "quit", "exit")
    HELP_CMDS = ("!h", "!help")
    FILE_CMDS = ("!gt", "!pt")
    SPECIAL_CMDS = ("!curl")
    NOT_TRACKED = ("||", "&&")
    MAX_PAYLOAD_SIZE = 6291456
    MAX_BODY_SIZE = MAX_PAYLOAD_SIZE - 500


    def __init__(self, addr, is_tracking_fs=False):
        self.addr = addr
        self.name = self.get_lambda_name()
        self.session = self.prepare_session()
        self.cwd = ""

        try:
            self.usr, self.cwd = self.init_shell()
        except (requests.exceptions.ConnectionError, requests.exceptions.InvalidURL) as err:
            print(colored(f"[!] Invalid URL or problem with connection: {self.addr}", "red", attrs=["bold"]))
            sys.exit(1)
        except requests.exceptions.MissingSchema as err:
            print(colored(f"[!] Missing schema from URL: {self.addr}", "red", attrs=["bold"]))
            sys.exit(1)
        except Exception as err:
            print(colored(err, "red", attrs=["bold"]))
            sys.exit(1)

        self.lambda_home_path = self.cwd
        self.prefix = self.usr + "@" + self.name + ":~"
        self.fs_state = self.verify_fs_state()
        self.print_fs_state_info()
        self.is_tracking_fs = is_tracking_fs and (self.fs_state.NEW_FS_CONT or self.fs_state.SAME_FS)

    def run(self):
        self.shell_loop()

    def shell_loop(self):
        while True:
            if self.is_tracking_fs:
                self.fs_state = self.verify_fs_state()
                self.print_fs_state_info()
                self.is_tracking_fs = self.is_tracking_fs and (self.fs_state.NEW_FS_CONT or self.fs_state.SAME_FS)

            prompt = colored(self.prefix, "green", attrs=["bold"]) + colored(self.cwd, "blue", attrs=["bold"]) + "$ "

            try:
                usr_input = input(prompt)
            except KeyboardInterrupt:
                print()
                continue
            except EOFError:
                print(colored("Exiting sHell!", 'cyan'))
                sys.exit(0)
            try:
                self.handle_input(usr_input.strip())
            except Exception as err:
                print(colored(err, "red", attrs=["bold"]))
                continue

    def handle_input(self, usr_input):
        if usr_input == "":
            return

        if usr_input in self.EXIT_CMDS:
            print(colored("Exiting sHell!", 'cyan'))
            sys.exit(0)

        if usr_input in self.HELP_CMDS:
            self.print_help()
            return

        if usr_input.startswith(self.FILE_CMDS):
            self.handle_file(usr_input)
            return

        if usr_input.startswith(self.SPECIAL_CMDS):
            self.handle_special(usr_input[1:])
            return

        if usr_input == "cd":
            self.cwd = self.lambda_home_path
            return

        if self.cwd != "" and self.cwd != self.lambda_home_path:
            cmd = "cd " + self.cwd + " && " + usr_input
        else:
            cmd = usr_input
        status, output = self.send_command(cmd)

        if status == Status.EXCEPTION:
            self.print_exception(output.decode("utf-8"))
            return

        print(output.decode("utf-8"))

        self.track_cwd(usr_input, (status != Status.OK))


    def track_cwd(self, usr_input, err):
        if ("cd" not in usr_input) or err:
            return

        if any(nt in usr_input for nt in self.NOT_TRACKED):
            print(colored("[-] Cannot track commands with '||' or '&&', current working directory not changed", "yellow"))
            return
        
        split_input = usr_input.split(" ")
        paths = [split_input[i + 1] for i, part in enumerate(split_input) if part == "cd"]

        for path in paths:
            if path[-1:] == ";":
                if path[-2:] != "\;":
                    path = path[:-1]

            if os.path.isabs(path):
                self.cwd = os.path.abspath(path)
            else:
                if path.startswith("~"):
                    path = self.lambda_home_path + path[1:]
                    self.cwd = os.path.abspath(path)
                else:
                    path = self.cwd + "/" + path
                    self.cwd = os.path.abspath(path)


    def init_shell(self):
        usr = self.get_user().decode("utf-8")
        cwd = self.get_pwd().decode("utf-8")
        return usr, cwd

    def get_user(self):
        status, output = self.send_command("whoami")
        if status == Status.OK:
            usr = output.rstrip()
        else:
            usr = ""
            print(colored("[-] Failed to get user name", "yellow"))
        return usr

    def get_pwd(self):
        if not self.cwd:
            cmd = "pwd"

        status, output = self.send_command(cmd)
        if status == Status.OK:
            cwd = output.rstrip()
        else:
            cwd = ""
            print(colored("[-] Failed to get Lambda initial path", "yellow"))
        return cwd

    def get_lambda_name(self):
        if "/" not in self.addr:
            return self.addr

        name = self.addr.split("/")[-1]
        if "?" not in name:
            return name
        
        return name.split("?")[0]

    def prepare_session(self):
        session = requests.Session()
        return session

    def handle_file(self, usr_input):
        args = usr_input.split(" ")
        if len(args) != 3:
            if args[0].startswith("!gt"):
                print(colored(f"[-] Usage `!gt <lambda-path> <local-path>`", "yellow"))
            elif args[0].startswith("!pt"):
                print(colored(f"[-] Usage `!pt <local-path> <lambda-path>`", "yellow"))
            return

        if args[0] == "!gt":
            self.getfile(args[1], args[2])
        elif args[0] == '!pt':
            self.putfile(args[1], args[2])
        else:
            print(colored("[-] handle_file - First argument need to be !gt or !pt", "yellow"))
            return

    def getfile(self, lambda_path, local_path):
        if os.path.isabs(lambda_path):
            path = lambda_path
        else:
            path = self.cwd + "/" + lambda_path
        print(colored(f"Downloading file from {path} ...", "cyan"))
        result, output = self.send_getfile_command(path)

        if result == Status.ERR:
            print(colored(output, "red"))

        elif result == Status.EXCEPTION:
            self.print_exception(output)
            
        else:
            to_decompress = False

            if result == Status.OK:
                write_mode = "w"
                output = output.decode("utf-8")

            elif result == Status.OK_BZ2:
                to_decompress = True
                local_path += ".bz2"
                write_mode = "wb"

            elif result == Status.OK_BIN:
                write_mode = "wb"

            try:
                writefile(local_path, write_mode, output)
            except IOError as err:
                print(colored(f"[!] Couldn't save file path {local_path} - IOError: {repr(err)}", "red"))
                return
        
            if to_decompress:
                try:
                    extract_bz2(local_path, local_path[:-4])
                    print(colored(f"Successfully decompressed file {local_path} to {local_path[:-4]}", "green"))
                except Exception as err:
                    print(colored(f"[!] Couldn't decompress obtained file\n{err}", "red"))
            
            print(colored(f"Copied {lambda_path} from Lambda to {local_path}", "green"))

    def putfile(self, local_path, lambda_path):
        if not os.path.exists(local_path):
            print(colored(f"[-] putfile - file {local_path} doesn't exist", "yellow"))
            return

        try:
            mode = check_type(local_path)
            is_compressed = False
            content = readfile(local_path, mode)

            if mode == "r":
                content = content.encode("utf-8")
            encoded = base64.b64encode(content).decode("utf-8")
            
            if len(encoded) < self.MAX_BODY_SIZE:
                result, output = self.send_putfile_command(lambda_path, encoded, mode, is_compressed)
            else:
                content_len = len(content)
                encoded_len = len(encoded)
                del content, encoded

                bz2_path = get_bz2_path(local_path)
                create_compressed_file(local_path, bz2_path)
                is_compressed = True
                lambda_path += ".bz2"

                content = readfile(bz2_path, "rb")
                os.unlink(bz2_path)

                encoded = base64.b64encode(content).decode("utf-8")
                if len(encoded) < self.MAX_BODY_SIZE:
                    result, output = self.send_putfile_command(lambda_path, encoded, "rb", if_compressed)
                else:
                    print(colored(f"[-] putfile - file {local_path} too big - Size: {content_len} | Encoded size: {encoded_len} | Compressed size: {len(content)} | Encoded compressed size: {len(encoded)}", "yellow"))
                    return
        except UnicodeDecodeError:
            print(colored(f"[!] putfile - file {local_path} failed with UnicodeDecodeError", "red"))
            return
        except IOError as err:
            print(colored(f"[!] putfile - file {local_path} failed with IOError: {repr(err)}", "red"))
            return
            
        if result == Status.ERR:
            print(colored(output, "red"))

        elif result == Status.EXCEPTION:
            self.print_exception(output)

        if is_compressed:
            print(colored(f"Compressed file {local_path} and copied to {lambda_path} on the Lambda", "green"))
        else:
            print(colored(f"File {local_path} copied to {lambda_path} on the Lambda", "green"))

    def send_command(self, cmd):
        data = self.messages.command_message(cmd)
        return self.send_request(data)

    def send_getfile_command(self, path):
        data = self.messages.getfile_message(path)
        return self.send_request(data)

    def send_putfile_command(self, path, content, mode, is_compressed):
        data = self.messages.putfile_message(path, content, mode, is_compressed)
        return self.send_request(data)

    def handle_special(self, cmd):
        data = self.messages.special_message(cmd)
        status, output = self.send_request(data)

        if status == Status.EXCEPTION:
            self.print_exception(output.decode("utf-8"))
            return

        print(output.decode("utf-8"))

    def send_request(self, data):
        response = self.session.post(self.addr, json=data)
        if not response:
            raise CommandException(f"[!] Didn't get response from the Lambda {self.addr}")
        try:
            response_json = json.loads(response.text)
        except json.decoder.JSONDecodeError as err:
            raise JSONDecodeError("[!] send_command - Couldn't decode JSON response from Lambda")

        status, output_b64 = self.parse_response(response_json)
        output = base64.b64decode(output_b64.encode("utf-8"))
        return status, output
        
    def parse_response(self, response_json):
        if "result" not in response_json:
            raise LackOfResult(f"[!] {sys._getframe(1).f_code.co_name} - Lack of 'result' field in Lambda response")

        if "output" not in response_json:
            raise LackOfOutput(f"[!] {sys._getframe(1).f_code.co_name} - Lack of 'output' field in Lambda response")

        return Status(response_json["result"]), response_json["output"]

    def verify_fs_state(self):
        status, _ = self.send_command("stat " + self.FS_TRACKER_PATH)
        if status == Status.OK:
            return FSState.SAME_FS
        if status == Status.EXCEPTION:
            print(colored("[-] Exception occured on Lambda site - cannot track Filesystem state", "yellow"))
            return FSState.EXCEPTION_FS

        status, _ = self.send_command("touch " + self.FS_TRACKER_PATH)
        if status != Status.OK:
            print(colored("[-] Filesystem tracker creation failed - cannot track Filesystem state", "yellow"))
            return FSState.NEW_FS_STOP
        
        return FSState.NEW_FS_CONT 

    def print_fs_state_info(self):
        if self.fs_state == FSState.SAME_FS:
            print(colored("Lambda Filesystem state from previous session preserved", "cyan"))
        elif self.fs_state != FSState.EXCEPTION_FS:
            print(colored("Lambda Filesystem reset / First time running with this Lambda", "yellow"))

    def print_exception(self, output):
        print(colored("[!] Lambda Handler encountered an unexpected exception while handling the command:", "red"))
        print(colored(output, "red"))

    def print_help(self):
        help_string = """
   __                 _         _                           _ _ 
  / /  __ _ _ __ ___ | |__   __| | __ _     ___   /\  /\___| | |
 / /  / _` | '_ ` _ \| '_ \ / _` |/ _` |   / __| / /_/ / _ \ | |
/ /__| (_| | | | | | | |_) | (_| | (_| |   \__ \/ __  /  __/ | |
\____/\__,_|_| |_| |_|_.__/ \__,_|\__,_|   |___/\/ /_/ \___|_|_|

A pseudo sHell for communicating with serverless container
\t # sHell on local machine.
\t # LaRE on serverless container (Lambda, Cloud Functions, Functions)

On a startup, 'whoami' and 'pwd' are executed to gain basic info about container.

# ----------------------------------------------------------------------------------- #

# How to use
\t > ./sHell.py [-h] [-fs] addr
\t > -h\tis for printing usage
\t > -fs\tis for enabling tracking filesystem*
\t > addr\tis URL address for connecting to the LaRE

\t * Tracking filesystem means verifying if the container is the same every executed command,
\t   by checking existance of temporary file in /tmp created on the startup

# Special commands in sHell:
\t > 'q' 'quit' 'exit'\t\t\t- to exit
\t > '!h' '!help'\t\t\t\t- to display this message
\t > '!gt <lambda-path> <local-path>'\t- to download file to your local machine
\t > '!pt <local-path> <lambda-path>'\t- to upload file to the serverless container
\t > '!curl <address>'\t\t\t- to request a resource in case of disabled original curl, uses urllib3 under the hood

# Limitations:
\t > File transfer limited to the Lambda's max request/response size (6MB). Bigger files are tried to be compressed.
\t > Does not support environment variables
\t > Limited support for CWD tracking.
\t   * Usage of '||' or '&&' breaks tracking, CWD won't be changed then
        """
        print(help_string)