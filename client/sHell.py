#!/usr/bin/env python3

from lib.pseudo_shell import PseudoShell
from lib.utils import parse_args


if __name__ == '__main__':
    sHell = PseudoShell(*parse_args())
    sHell.run()
