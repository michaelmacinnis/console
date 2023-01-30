import tty

import debug

control_modes = {
    tty.CSIZE: "Character size",
    tty.CSTOPB: "Send two stop bits, else one",
    tty.CREAD: "Enable receiver",
    tty.PARENB: "Parity enable",
    tty.PARODD: "Odd parity, else even",
    tty.HUPCL: "Hang up on last close",
    tty.CLOCAL: "Ignore modem status lines",
}

input_modes = {
    tty.BRKINT: "Signal interrupt on break",
    tty.ICRNL: "Map CR to NL on input",
    tty.IGNBRK: "Ignore break condition",
    tty.IGNCR: "Ignore CR",
    tty.IGNPAR: "Ignore characters with parity errors",
    tty.INLCR: "Map NL to CR on input",
    tty.INPCK: "Enable input parity check",
    tty.ISTRIP: "Strip character",
    tty.IXANY: "Enable any character to restart output",
    tty.IXOFF: "Enable start/stop input control",
    tty.IXON: "Enable start/stop output control",
    tty.PARMRK: "Mark parity errors",
}

local_modes = {
    tty.ECHO: "Enable echo",
    tty.ECHOE: "Echo erase character as error-correcting backspace",
    tty.ECHOK: "Echo KILL",
    tty.ECHONL: "Echo NL",
    tty.ICANON: "Canonical input (erase and kill processing)",
    tty.IEXTEN: "Enable extended input character processing",
    tty.ISIG: "Enable signals",
    tty.NOFLSH: "Disable flush after interrupt or quit",
    tty.TOSTOP: "Send SIGTTOU for background output",
}

output_modes = {
    tty.OPOST: "Post-process output",
    tty.ONLCR: "Map NL to CR-NL on output",
    tty.OCRNL: "Map CR to NL on output",
    tty.ONOCR: "No CR output at column 0",
    tty.ONLRET: "NL performs CR function",
    tty.OFILL: "Use fill characters for delay",
    tty.NLDLY: "Newline delay",
    tty.CRDLY: "Carriage-return delay",
    tty.TABDLY: "Horizontal-tab delay",
    tty.BSDLY: "Backspace delay",
    tty.VTDLY: "Vertical-tab delay",
    tty.FFDLY: "Form-feed delay",
}


def print(lst):
    debug.log("mode change:")

    modes = [input_modes, output_modes, control_modes, local_modes]
    for i in range(4):
        flags = lst[i]
        for flag, description in modes[i].items():
            if flag & flags:
                debug.log(description)

    debug.log()
