class Messages:

    OP = "action"
    ARGS = "args"


    def command_message(self, cmd):
        return {OP: "cmd", ARGS: ["bash", "-c", cmd]}