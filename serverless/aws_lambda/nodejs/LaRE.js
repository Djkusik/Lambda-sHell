const utils = require('./utils')
const { spawn } = require('child_process');


exports.handler = async function(event, context) {
    let action, data, resp_type, result, output;
    console.log("[+] LaRE is starting");
    try {
        [action, data] = parse_event(event);
        if (action === utils.CMD_OP) {
            run_cmd(data, (result, output) => {
                if (result === 0) {
                    result = utils.Status.OK;
                } else {
                    result = utils.Status.ERR;
                }
                return construct_response(result, output.toString('base64'));
            })
        } else if (action === utils.SPECIAL_OP) {
            run_special(data, (result, output) => {
                return construct_response(result, output.toString('base64'));
            })
        } else if (action === utils.GET_FILE_OP) {
            [result, output] = run_getfile(data);
        } else if (action === utils.PUT_FILE_OP) {
            [result, output] = run_putfile(data);
        }

        return construct_response(resp_type, result, output);
    } catch(err) {
        return construct_response(utils.Status.EXCEPTION, Buffer.from(err.message).toString('base64'));
    }

}

function parse_event(event) {
    let action;
    if (event.body !== null && event.body !== undefined) {
        let body = JSON.parse(event.body);
    } else {
        console.log(event);
        throw new Error('[!] parse_event - lack of event.body}');
    }

    if (utils.OP in body && utils.ARGS in body) {
        if (body[utils.OP] === utils.CMD_OP) {
            action = utils.CMD_OP;
        } else if (body[utils.OP] === utils.GET_FILE_OP) {
            action = GET_FILE_OP;
        } else if (body[utils.OP] === utils.PUT_FILE_OP) {
            action = PUT_FILE_OP;
        } else if (body[utils.OP] === utils.SPECIAL_OP) {
            action = utils.SPECIAL_OP;
        } else {
            throw new Error(`[!] parse_event - Unknown operation ${body[utils.OP]}`);
        }
        return [action, body[utils.ARGS]];
    } else {
        throw new Error(`[!] parse_event - Lack of operation and / or args ${body}`);
    }

}

function run_cmd(cmd, callback) {
    let proc = spawn(cmd[0], cmd.slice(1));
    proc.stderr.pipe(process.stdout);
    var output;

    proc.stdout.on('data', (data) => {
        output = data;
    })

    proc.on('close', (rc) => {
        callback(rc, output);
    })
}

function run_special(cmd, callback) {
    if (cmd.startsWith('curl')) {
        return curl(cmd, callback);
    }
}

function curl(cmd, callback) {
    addr = cmd.split(' ')[1]
    if (addr.substring(0, 5) === "https") {
        const req = require('https');
    } else {
        const req = require('http');
    }
    req.get(addr, (resp) => {
        let data = '';

        resp.on('data', (chunk) => {
            data += chunk;
        });

        resp.on('end', () => {
            callback(utils.Status.OK, data);
        })
    }).on("error", (err) => {
        throw new Error(`[!] curl - Some error when using http/s module: ${(err.message)}`);
    })
}

function run_getfile(path) {

}

function run_putfile(path) {

}

function construct_response(result, output) {
    let response = {
        statusCode: 200,
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            "result": result,
            "output": output
        })
    };
    return response;
}