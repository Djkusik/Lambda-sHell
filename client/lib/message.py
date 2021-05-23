class Messages:

    OP = "action"
    ARGS = "args"


    def command_message(self, cmd):
        return {
            self.OP: "cmd", 
            self.ARGS: ["bash", "-c", cmd]
        }

    def special_message(self, cmd):
        return {
            self.OP: "special",
            self.ARGS: cmd
        }

    def getfile_message(self, path):
        return {
            self.OP: "getfile", 
            self.ARGS: path
        }

    def putfile_message(self, path, content, mode, is_compressed):
        return {
            self.OP: "putfile", 
            self.ARGS: {
                "path": path, 
                "content": content, 
                "mode": mode, 
                "is_compressed": is_compressed
            }
        }