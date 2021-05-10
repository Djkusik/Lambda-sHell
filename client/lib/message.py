class Messages:

    OP = "action"
    ARGS = "args"


    def command_message(self, cmd):
        return {OP: "cmd", ARGS: ["bash", "-c", cmd]}

    def getfile_message(self, path):
        return {OP: "getfile", ARGS: path}

    def putfile_message(self, path, content):
        return {OP: "putfile", ARGS: {"path": path, "content": content}}