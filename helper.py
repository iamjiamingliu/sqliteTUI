from prettytable import PrettyTable, from_db_cursor
from typing import *
import sys, os, sqlite3, time, traceback, math
from threading import Thread
import textwrap, tty, termios, click


def indent(text, amount, ch=' '):
    return textwrap.indent(text, amount * ch)


class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def color_print(color, *args, **kwargs):
    print(color, *args, Colors.ENDC, **kwargs)


TITLE = \
    f"""
  ==================================================
   {Colors.GREEN}WELCOME To Sqlite Text User Interface!{Colors.ENDC}
                                     @ 2021 Jay Leo    
  ==================================================
    """

BYE = \
    f"""
  ==================================================
   {Colors.GREEN}Thank you for using Sqlite Text User Interface!{Colors.ENDC}
                                     @ 2021 Jay Leo    
  ==================================================
    """

INVALID_INPUT = f">>> {Colors.RED}Invalid Option.{Colors.ENDC} Try again: "

OPTION_HELP = \
    f"""
  ==========================================================
   HELP Notes
   to select an option, simply enter the acronym of an option
   to illustrate, if you see something like:
        [{Colors.CYAN}A{Colors.ENDC}]pple    [{Colors.CYAN}B{Colors.ENDC}]anana    [{Colors.CYAN}Ap{Colors.ENDC}]ple Computer
        [{Colors.CYAN}Bo{Colors.ENDC}]ttled water
   and wants to choose "Apple computer", simply type {Colors.CYAN}ap{Colors.ENDC}
   (case insensitive) and hit enter
  ==========================================================
    """


def create_table(column_names: List, data: List[List]):
    table = PrettyTable()
    table.field_names = column_names
    table.add_rows(data)
    return table


def strinfy(num: int):
    conversion = {1e15: 'PB', 1e12: 'TB', 1e9: 'GB', 1e6: 'MB', 1e3: 'KB'}
    for c in conversion:
        if num // c:
            return "{:.2f}".format(num / c) + ' ' + conversion[c]


def get_option(options: Iterable[str], line_width=60, separator='  ', spread_out=True, indentation=2):
    """options must not contain strings shorter than 2 length, and separator must NOT be ' '"""
    cur_width = 0
    prompts = [""]
    used = set()
    acronyms = {}

    def spread(line: str):
        c = line.count(separator)
        if c and c * 2 + len(line) <= line_width:
            spaces = int((line_width - len(line)) / c / 2)
            line = line.replace(separator, ' ' * spaces + separator + ' ' * spaces)
        return line

    for option in options:
        if not option:
            continue
        if cur_width + len(option) + 1 + len(separator) > line_width:
            prompts[-1] = prompts[-1].rstrip()
            if spread_out:
                prompts[-1] = spread(prompts[-1])
            prompts.append("")
            cur_width = 0
        for i in range(len(option)):
            if option[:i + 1].capitalize() not in used:
                prompts[-1] += f'[{Colors.CYAN}{option[:i + 1].capitalize()}{Colors.ENDC}]' + option[i + 1:] + separator
                cur_width += len(option) + 2 + len(separator)
                acronyms[option[:i + 1].capitalize()] = option
                used.add(option[:i + 1].capitalize())
                break
    prompts[-1] = prompts[-1].rstrip()
    prompts[-1] = spread(prompts[-1])
    prompt = indent('\n'.join(prompts), indentation)
    ipt = input(
        ' ' * indentation + 'Below are the options you have: \n\n' + prompt + '\n\n' + ' ' * indentation + f'>>> Enter an option ({Colors.CYAN}h{Colors.ENDC} for help): ').lower()
    while ipt == 'h' or ipt.capitalize() not in acronyms:
        if ipt == 'h':
            print(' ' * indentation + OPTION_HELP)
            ipt = input(' ' * indentation + f'>>> Enter an option ({Colors.CYAN}h{Colors.ENDC} for help): ').lower()
        else:
            ipt = input(' ' * indentation + INVALID_INPUT).lower()
    return acronyms[ipt.capitalize()]


def get_text_input(prompt, indentation=2):
    """prompt should NOT include : at the end"""
    ipt = input(
        '\n' + ' ' * indentation + prompt + f' (or enter {Colors.CYAN}b{Colors.ENDC} to go back):\n' + ' ' * indentation)
    if ipt.lower().strip() == 'b':
        return
    return ipt


class Spinner:
    def __init__(self, isLoading=True, start=True):
        self.isLoading = isLoading
        if start:   self.start()

    def get_spinners(self):
        while 1:
            for cursor in '|/-\\':
                yield cursor

    def start(self, isThreaded=True):
        def _start_helper():
            spinners = self.get_spinners()
            while self.isLoading:
                sys.stdout.write(next(spinners))
                sys.stdout.flush()
                time.sleep(0.1)
                sys.stdout.write('\b')

        if isThreaded:
            Thread(target=_start_helper).start()
        else:
            _start_helper()

    def stop(self):
        self.isLoading = False


printable = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~'


def get_arrow_input(indentation=2):
    print(' ' * indentation, end='')
    c = click.getchar()
    if c == '\x1b[D':
        return 'left'
    if c == '\x1b[C':
        return 'right'
    if c == '\x1b[A':
        return 'up'
    if c == '\x1b[B':
        return 'down'
    return ''.join(['\\' + hex(ord(i))[1:] if i not in printable else i for i in c])
