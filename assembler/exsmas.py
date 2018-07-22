#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Extended SMA16 Assembler."""

__author__ = "Jacob Allen"
__version__ = "0.1.0alpha"

import argparse
import sys

#from exsmas import base_instructions, extension_instructions


def debug(*args, **kwargs):
    """Print debug messages."""
    if kwargs.get("debug", True):
        print(args)


def main():
    """Run the Extended SMA16 Assembler."""
    argument_parser = argparse.ArgumentParser(
        description=
        "The extended SMA16 assembler provides a more fully featured assembly\
        language for the SMA16 virtual architecture.\
        Common instructions such as `subtract` and `bitwise or` are provided.",
        add_help=True)
    argument_parser.add_argument(
        "-v",
        "--version",
        action="store_true",
        help="show a version message and exit")
    argument_parser.add_argument(
        "-d", "--debug", action="store_true", help="show debug messages")
    argument_parser.add_argument(
        "-o", "--output", type=str, help="specify output file path")
    argument_parser.add_argument(
        "-i", "--input", type=str, help="specify input file path")
    argument_parser.add_argument(
        "-", dest="stdin", action="store_true", help="read from stdin")
    parsed_args = argument_parser.parse_args()

    if parsed_args.version:
        print("Extended SMA16 Assembler [v{version}] by {author}".format(
            version=__version__, author=__author__))
        return 0

    argument_parser.print_usage()
    return 0


if __name__ == "__main__":
    sys.exit(main())
