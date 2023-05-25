#! /usr/bin/env python3
"""Wrap the clipboard with a function specified as a cmd line arg (if fun from run
window) or via user interface is run from listener_standard script."""
import functools
import logging
import re
from typing import List

import pyperclip
from pynput.keyboard import Key
from textblob import TextBlob

from clmac.typer import Typer

logger = logging.getLogger(__name__)

typer = Typer()
LINE_CHAR_LIMIT = 88


def clipboard_in_out(func):
    """Decorator that grabs text from the clipboard passes it to the decorated function
    then copies the text returned by the decorated function to the clipboard."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        clip: str = pyperclip.paste().strip()
        time.sleep(0.1)
        clip = func(clip)
        pyperclip.copy(clip)
        typer.type_text(clip)

    return wrapper


def clipboard_in_out_paste(func):
    """Decorator that grabs text from the clipboard passes it to the decorated function
    then copies the text returned by the decorated function to the clipboard."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        clip: str = pyperclip.paste().strip()
        time.sleep(0.1)
        clip = func(clip)
        pyperclip.copy(clip)
        typer.paste()

    return wrapper


# transforms that do not add or remove characters ######################################


@clipboard_in_out_paste
def to_lower(s: str) -> str:
    return s.lower()


@clipboard_in_out_paste
def to_upper(s: str) -> str:
    return s.upper()


@clipboard_in_out_paste
def to_capitalize(s: str) -> str:
    return s.capitalize()


@clipboard_in_out
def split_join(name: str) -> str:
    return " ".join(name.split())


@clipboard_in_out
def wrap_text(s: str, max_len: int = 88) -> str:
    """Wrap text to a maximum line length."""
    s.fill(s, width=max_len).strip()
    return s


@clipboard_in_out_paste
def spell_check(s: str) -> str:
    sentence = TextBlob(s)
    corrected = sentence.correct()
    return str(corrected)


@clipboard_in_out
def to_snake(text: str) -> str:
    lines = [re.sub("[\s_]+", "_", line).lower() for line in text.splitlines()]
    return "\n".join(lines)


@clipboard_in_out
def remove_blanklines(s: str) -> str:
    """Remove blank lines from a block of text and return it to the clipboard.

    input
    -----
    hello

    world

    output
    ------
    hello
    world
    """
    lines = [x.strip() for x in s.split("\n") if not x.isspace()]
    lines = list(filter(None, lines))
    lines = "\n".join(lines)
    return lines


@clipboard_in_out
def to_list(s: str) -> str:
    """Format a sequence separated by white space into a python list format.

    input
    -----
    hello there

    output
    ------
    'hello', 'there'
    """
    output = ", ".join([f"'{chars}'" for chars in s.split()]) + ","
    return output


@clipboard_in_out_paste
def underline(s: str) -> str:
    """Add a dash underline to the clipboard item and return to the clipboard.

    input
    -----
    moje is a goon

    output
    ------
    moje is a goon
    --------------
    """
    output = s + "\n" + create_underline(s)
    return output


def create_underline(text: str) -> str:
    clipboard_clean: str = " ".join(text.split())
    return len(clipboard_clean) * "-"


@clipboard_in_out_paste
def format_variables(s: str) -> str:
    """Take the variables from the clipboard and format them as a string to be printed
    and return to clipboard.

    input
    ------
    days_elapsed
    weeks_elapsed

    output
    -----
    print(f'days_elapsed={days_elapsed}',
        f'weeks_elapsed={weeks_elapsed}')
    """
    variables = re.sub("[^\w\s]", "", s).split()
    variables = [f"{v}={{{v}:}}" for v in variables]
    output = f"print(f'{', '.join(variables)}')"
    if len(output) > 88:
        output = "', \n      f'".join(output.split(", "))
    return output


# padding formatters ###################################################################


def _pad_right_full(s: str, char: str, left_len: int = 1) -> str:
    """Add a left justify fill of hash characters to the current clipboard item to a
    length of 88 character and return it to the clipboard.

    pad_right_full('#')
    input:
    hello world
    output:
    # hello world ##########################################################################
    """
    s = s[:LINE_CHAR_LIMIT]
    s = f"{char * left_len} " + s.strip(f"#- ") + " "
    output = s.ljust(LINE_CHAR_LIMIT, f"{char}")
    return output


@clipboard_in_out_paste
def format_hash(s: str) -> str:
    """See: pad_right_full()"""
    return _pad_right_full(s, "#")


@clipboard_in_out_paste
def format_dash(s: str) -> str:
    """See: pad_right_full()"""
    return _pad_right_full(s, "-", left_len=2)


@clipboard_in_out_paste
def format_hash_center(s: str) -> str:
    """Add a center justify fill of hash characters to the current clipboard item to a
    length of 88 character and return it to the clipboard.

    input:
    hello world
    output:
    ##################################### hello world ######################################
    """
    s = s[:LINE_CHAR_LIMIT]
    s = " " + s.strip() + " "
    output = f"{s:#^88}"
    return output


# specific use case string formatters ##################################################


@clipboard_in_out
def wrap_fstring(s: str) -> str:
    wrapped = "f'{" + s + "}'"
    pyperclip.copy(wrapped)
    typer.paste()
    typer.press_key(Key.left, num_presses=len(s) + 3)
    return wrapped


@clipboard_in_out
def unnest_parathesis(s: str) -> str:
    """Extract the content of the paraenthesis from the current clipboard selection and
    type it out.

    input:
    print(''.join('hello world'))
    output:
    ''.join('hello world')
    """
    s = s.strip()
    inner = re.search("\(.+\)", s)
    if inner:
        inner = inner.group(0)[1:-1]
    else:
        inner = s
    return inner


@clipboard_in_out
def format_repr(s: str) -> str:
    """Copy class properties to the clipboard, run this program, and it will format the
    properties as a human readable repr string that you can add to your class.

    input from clipboard:
        self.id = id_
        self.username = username
        self.password = password
    output of script:
        (id=self.id, username=self.username, password=self.password)
    """
    logger.info(f"clipped: {s}")
    lines = [x for x in s.split("\n") if not x.isspace()]
    test_valid_input(lines)
    properties = [x.split(".")[1].strip() for x in lines]
    names = [x.split("=")[0].strip() for x in properties]
    output_text: str = (
        "(" + ", ".join([f"{name}={{self.{name}}}" for name in names]) + ")"
    )
    output_text: str = (
        f"def __repr__(self):\n\treturn f'{{self.__class__.__name__}}{output_text}'"
    )
    return output_text


def test_valid_input(lines: List[str]) -> None:
    if not any(["." in line for line in lines]):
        raise InvalidInputError("Are you using the correct input? eg self.name = name")


class InvalidInputError(TypeError):
    pass


@clipboard_in_out_paste
def imports_to_requirements(s: str) -> str:
    """

    input
    -----
    import requests
    from lxml import html
    from plotly.offline import plot
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By

    output
    ------
    lxml
    requests
    plotly
    selenium
    """
    modules = set([re.split(r"[ .]", line)[1] for line in s.splitlines() if line])
    return "\n".join(modules)


# select line first formatters #########################################################


def set_equal_to_self() -> None:
    """Select text on the current line copy it and set it equal to itself
    in: df
    out: df = df"""
    text = typer.select_line_at_caret_and_copy()()
    typer.caret_to_line_end()
    typer.type_text(" = " + text)
    logger.info(f"typed: {text}")


def cut_right_equality() -> None:
    """Cut the right side of the equality and add to clipboard.

    in: greeting = 'hello world'
    out: greeting =
    """
    line = typer.select_line_at_caret_and_copy()()
    left, right = line.split("=", maxsplit=1)
    pyperclip.copy(right.strip())
    typer.type_text(left + "= ")