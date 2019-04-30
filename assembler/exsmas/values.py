#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Provides values for use with instructions."""

from typing import Union


class ConstantValue:
    """Constant values for use with instructions."""

    def __init__(self, value: Union[int, str]) -> None:
        """Initialise Constant Value."""
        if isinstance(value, int):
            self.value = value
        elif isinstance(value, str) and len(value) == 1:
            self.value = ord(value)
        else:
            raise ValueError("Value must be a char or an 12-bit int")

    def get_hex(self) -> str:
        """Get the hex representation of the value."""
        return "0x%03x" % self.value

    def get_int(self) -> int:
        """Get the int value of the constant."""
        return self.value
