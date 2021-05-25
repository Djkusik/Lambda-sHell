const Status = {
    OK: 1,
    ERR: 2,
    EXCEPTION: 3,
    OK_BIN: 4,
    OK_BZ2: 5
}

const read_to_write = {
    "r": "w",
    "rb": "wb"
}

module.exports = {
    OP = "action",
    CMD_OP = "cmd",
    SPECIAL_OP = "special",
    GET_FILE_OP = "getfile",
    PUT_FILE_OP = "putfile",
    ARGS = "args",
    MAX_PAYLOAD_SIZE = 6291456,
    MAX_BODY_SIZE = MAX_PAYLOAD_SIZE - 500,
    SPECIAL_CMDS = ["curl"],
    Status: Status,
    read_to_write: read_to_write
}

