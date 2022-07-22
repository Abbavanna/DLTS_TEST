import datetime as dt
import functools
import sys
import traceback


class DebugColors:
    DEBUG1 = '\033[1;97;100m'       # Bold, Intense Black BG, White Text
    DEBUG2 = '\033[1;90;101m'       # Bold, Intense Red BG, Black Text
    DEBUG3 = '\033[1;90;102m'       # Bold, Intense Green BG, Black Text
    DEBUG4 = '\033[1;90;103m'       # Bold, Intense Yellow BG, Black Text
    DEBUG5 = '\033[1;90;104m'       # Bold, Intense Blue BG, Black Text
    DEBUG6 = '\033[1;97;105m'       # Bold, Intense Purple BG, White Text
    DEBUG7 = '\033[1;90;106m'       # Bold, Intense Cyan BG, Black Text
    DEBUG8 = '\033[1;90;107m'       # Bold, Intense White BG, Black Text
    ENDC   = '\033[0m'              # None

    def disable(self):
        self.DEBUG1 = ''
        self.DEBUG2 = ''
        self.DEBUG3 = ''
        self.DEBUG4 = ''
        self.DEBUG5 = ''
        self.DEBUG6 = ''
        self.DEBUG7 = ''
        self.DEBUG8 = ''


STYLES = {
    'debug': DebugColors.DEBUG1,
    'debug_k': DebugColors.DEBUG1,
    'debug_r': DebugColors.DEBUG2,
    'debug_g': DebugColors.DEBUG3,
    'debug_y': DebugColors.DEBUG4,
    'debug_b': DebugColors.DEBUG5,
    'debug_p': DebugColors.DEBUG6,
    'debug_c': DebugColors.DEBUG7,
    'debug_w': DebugColors.DEBUG8,
}


def cprint(text, style=None):
    style = STYLES.get(style, None)
    if style:
        print(f"{style}{text}{DebugColors.ENDC}")
    else:
        print(f"{text}")

