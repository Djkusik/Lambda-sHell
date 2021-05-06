import requests
import json
import sys
import base64

from termcolor import colored
from .message import Messages
from .exceptions import *
from .utils import *

class PseudoShell:

    messages = Message()
    FS_TRACKER_PATH = "/tmp/.sHell_tracker"
    EXIT_CMDS = ["q", "quit", "exit"]
    HELP_CMDS = ["!h", "!help"]


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
        self.prefix = self.usr + "@" + self.name + ":~/"
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
                self.is_tracking_fs = is_tracking_fs and (self.fs_state.NEW_FS_CONT or self.fs_state.SAME_FS)

            prompt = colored(self.prefix, "green") + colored(self.cwd, "blue") + "$ "

            try:
                usr_input = input(prompt)
            except KeyboardInterrupt:
                print()
                continue
            except EOFError:
                print(colored("Exiting sHell!", 'cyan'))
                sys.exit(0)
            
            self.handle_input(usr_input.strip())

    def handle_input(self, usr_input):
        if usr_input == "":
            return

        if usr_input in self.EXIT_CMDS:
            print(colored("Exiting sHell!", 'cyan'))
            sys.exit(0)

        if usr_input in self.HELP_CMDS:
            #TODO Create print help
            return

        if usr_input == "cd":
            self.cwd = self.lambda_home_path
            return

        #TODO Get/Put file
        
        if self.cwd != "" and self.cwd != self.lambda_home_path:
            cmd = "cd " + self.cwd + " && " + usr_input
        else:
            cmd = usr_input
        status, output = self.send_command(cmd)

        if status == Status.EXCEPTION:
            print(colored("[!] Lambda Handler encountered an unexpected exception while handling the command:", 'red'))
            print(colored(output, ''))
            return

        print(self.decode_output(output))

        #TODO CWD Tracking
        
    def decode_output(self, output):
        if type(output) is bytes:
            output = str(output)[2:-1]
        return output

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

    def init_shell(self):
        usr = self.get_user()
        cwd = self.get_pwd()
        return usr, cwd

    def get_user(self):
        status, output = self.send_command("whoami")
        if status == Status.OK:
            usr = output.rstrip()
        else:
            usr = ""
            print(colored("[-] Failed to get user name", 'yellow'))
        return usr

    def get_pwd(self):
        if not self.cwd:
            cmd = "pwd"

        status, output = self.send_command(cmd)
        if status == Status.OK:
            cwd = output.rstrip()
        else:
            cwd = ""
            print(colored("[-] Failed to get Lambda initial path", 'yellow'))
        return cwd

    def send_command(self, cmd):
        data = messages.command_message(cmd)
        try:
            response = self.session.post(self.addr, json=data)
        if not response:
            raise CommandException(f"[!] Didn"t get response from the Lambda {self.addr}")

        try:
            response_json = json.loads(resp.text)
        except json.decoder.JSONDecodeError as err:
            raise JSONDecodeError("[!] send_command - Couldn't decode JSON response from Lambda")

        status, output_b64 = self.parse_response(response_json)
        output = base64.b64decode(bytes(output_b64, "ascii"))
        return status, output
        
    def parse_response(self, response_json):
        if "result" not in response_json:
            raise LackOfResult(f"[!] {sys._getframe(1).f_code.co_name} - Lack of "result" field in Lambda response")

        if "output" not in response_json:
            raise LackOfOutput(f"[!] {sys._getframe(1).f_code.co_name} - Lack of "output" field in Lambda response")

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