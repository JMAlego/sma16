#!/usr/bin/env python3
"""SMA16 assembler."""
from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser
from dataclasses import dataclass
from difflib import get_close_matches
from enum import IntEnum
from os import path
from struct import pack as struct_pack
from sys import stderr, stdout
from typing import Dict, Iterable, Iterator, List, Optional, Set, Tuple, Union


class AssemblyError(Exception):
    """All assembly errors."""


class Instruction(IntEnum):
    """Machine instructions."""

    HALT = 0x0
    # 0x1
    JUMP = 0x2
    JUMPZ = 0x3
    LOAD = 0x4
    STORE = 0x5
    LSHFT = 0x6
    RSHFT = 0x7
    XOR = 0x8
    AND = 0x9
    SFULL = 0xA
    ADD = 0xB
    # 0xC
    POP = 0xD
    PUSH = 0xE
    NOOP = 0xF


@dataclass
class ParsedValue:
    """A freshly parsed value."""

    type: str
    value: Union[int, str]


@dataclass
class ParsedInstruction:
    """A freshly parsed instruction."""

    name: str
    value: Optional[ParsedValue]
    labels: Set[str]
    section: str
    line: int


@dataclass
class ParsedDirective:
    """A freshly parsed directive."""

    name: str
    value: Optional[ParsedValue]
    labels: Set[str]
    section: str
    line: int


@dataclass
class ParsedLabel:
    """A freshly parsed label."""

    name: str


ParsedItem = Union[ParsedInstruction, ParsedDirective, ParsedLabel]
GluedItem = Union[ParsedInstruction, ParsedDirective]


@dataclass
class Vector:
    """An interrupt vector."""

    address: int
    max_length: int


@dataclass
class Register:
    """A hardware register."""

    address: int


@dataclass
class Region:
    """A memory region."""

    type: str
    start: int
    end: int
    count: int


MemoryTable = Dict[int, int]
ReferenceTable = Dict[str, int]
RegionTable = Dict[str, Region]


@dataclass
class AddressValue:
    """A value stored at an address."""

    address: int
    value: int


def did_you_mean(name: str, reference_table: ReferenceTable) -> str:
    """Create a 'did you mean x?' string."""
    close_matches = get_close_matches(name, reference_table.keys(), n=1, cutoff=0.75)
    if close_matches:
        return ", did you mean {}?".format(close_matches[0])
    return ""


@dataclass
class UnresolvedAddressValue:
    """An unresolved value stored at an address."""

    address: int
    instruction: Instruction
    data: str

    def resolve(self, reference_table: ReferenceTable) -> AddressValue:
        """Resolve the address value given a reference table."""
        if self.data not in reference_table:
            raise AssemblyError("reference to undefined location {}{}".format(self.data,
                                                                              did_you_mean(self.data, reference_table)))
        value = (reference_table[self.data] & 0x0fff) | ((self.instruction.value << 12) & 0xf000)
        return AddressValue(address=self.address, value=value)


@dataclass
class UnresolvedAddressConstant:
    """An unresolved value stored at an address."""

    address: int
    value: str

    def resolve(self, reference_table: ReferenceTable) -> AddressValue:
        """Resolve the address value given a reference table."""
        if self.value not in reference_table:
            raise AssemblyError("reference to undefined location {}{}".format(self.value,
                                                                              did_you_mean(self.value,
                                                                                           reference_table)))
        return AddressValue(address=self.address, value=reference_table[self.value])


def force_resolved(generator_function):
    """Turn a generator function into a normal function returning a list."""

    def resolver_function(*args, **kwargs):
        return list(generator_function(*args, **kwargs))

    return resolver_function


VECTORS = {
    "reset": Vector(address=0x000, max_length=1),
    "fault": Vector(address=0x001, max_length=1),
    "software": Vector(address=0x002, max_length=6)
}

REGISTERS = {
    "INTERRUPT_REASON": Register(address=0x008),
    "INTERRUPT_RETURN": Register(address=0x009),
    "ASCII_OUT": Register(address=0x00A),
    "SMALL_OUT": Register(address=0x00B),
    "TERM_CONF": Register(address=0x00C),
    "STACK_SIZE": Register(address=0x00D),
    "RESERVED1": Register(address=0x00E),
    "RESERVED2": Register(address=0x00F)
}

REGIONS = {
    "configuration": Region(type="reserved", start=0x008, end=0x00f, count=8),
    "vectors": Region(type="reserved", start=0x000, end=0x007, count=8),
}

CONSTANTS = {
    "RESET_VECTOR": VECTORS["reset"].address,
    "FAULT_VECTOR": VECTORS["fault"].address,
    "SOFTWARE_VECTOR": VECTORS["software"].address,
    **{key: value.address
       for (key, value) in REGISTERS.items()}
}


def _is_c_name(to_test: str):
    return all(map(str.isalnum, filter(len, to_test.split("_")))) and not to_test[0].isnumeric()


def get_file_lines(file_path: str) -> Iterator[str]:
    """Get lines of a file."""
    with open(file_path, "r") as file_handle:
        for line in file_handle:
            yield line


def parse_line(line: str, line_number: int) -> Iterator[ParsedItem]:
    """Parse a line."""
    line = line.strip()
    if line and not line.startswith("#"):
        keep_checking_for_labels = True
        while keep_checking_for_labels and ":" in line:
            label, *rest = line.split(":")
            if _is_c_name(label):
                line = ":".join(rest).strip()
                yield ParsedLabel(name=label)
            else:
                keep_checking_for_labels = False

        if line.startswith("."):
            name, *value = line.split(" ")
            yield ParsedDirective(name=name,
                                  value=parse_value(" ".join(value), line_number),
                                  labels=set(),
                                  section="any",
                                  line=line_number)
        elif line:
            name, *value = line.split(" ")
            yield ParsedInstruction(name=name,
                                    value=parse_value(" ".join(value), line_number),
                                    labels=set(),
                                    section="any",
                                    line=line_number)


def parse_value(to_parse: str, line_number: int) -> Optional[ParsedValue]:
    """Parse a value."""
    to_parse = to_parse.strip()

    if not to_parse:
        return None

    if to_parse.lower() == "?":
        return ParsedValue(type="integer", value=0)

    if to_parse.startswith("@"):
        if not _is_c_name(to_parse[1:]):
            raise AssemblyError("reference name invalid {} on line {}".format(to_parse[1:], line_number))
        return ParsedValue(type="reference", value=to_parse[1:])

    if to_parse.startswith("0x"):
        return ParsedValue(type="integer", value=int(to_parse, 16))

    if to_parse.startswith("0b"):
        return ParsedValue(type="integer", value=int(to_parse, 2))

    if to_parse.isdigit():
        return ParsedValue(type="integer", value=int(to_parse, 10))

    if to_parse.startswith("s\""):
        try:
            eval_value = eval(to_parse[1:])
        except SyntaxError:
            raise AssemblyError("invalid small string {} on line {}".format(to_parse[1:], line_number))
        if not isinstance(eval_value, str) or len(eval_value) != 2:
            raise AssemblyError("invalid small string value {} on line {}".format(to_parse[1:], line_number))
        return ParsedValue(type="short_string", value=eval_value)

    if to_parse.startswith("a\""):
        try:
            eval_value = eval(to_parse[1:])
        except SyntaxError:
            raise AssemblyError("invalid ascii string {} on line {}".format(to_parse[1:], line_number))
        if not isinstance(eval_value, str) or len(eval_value) != 2:
            raise AssemblyError("invalid ascii string value {} on line {}".format(to_parse[1:], line_number))
        return ParsedValue(type="ascii_string", value=eval_value)

    if to_parse.startswith("s'"):
        try:
            eval_value = eval(to_parse[1:])
        except SyntaxError:
            raise AssemblyError("invalid short character {} on line {}".format(to_parse[1:], line_number))
        if not isinstance(eval_value, str) or len(eval_value) != 1:
            raise AssemblyError("invalid short character value {} on line {}".format(to_parse[1:], line_number))
        return ParsedValue(type="short_character", value=eval_value)

    if to_parse.startswith("a'"):
        try:
            eval_value = eval(to_parse[1:])
        except SyntaxError:
            raise AssemblyError("invalid ascii character {} on line {}".format(to_parse[1:], line_number))
        if not isinstance(eval_value, str) or len(eval_value) != 1:
            raise AssemblyError("invalid ascii character value {} on line {}".format(to_parse[1:], line_number))
        return ParsedValue(type="ascii_character", value=eval_value)

    return ParsedValue(type="raw_value", value=to_parse)


def parse_lines(file_path: str) -> Iterator[ParsedItem]:
    """Parse all lines in a file."""
    for line_number, line in enumerate(get_file_lines(file_path), start=1):
        yield from parse_line(line, line_number)


def glue_labels_and_sections(items: Iterable[ParsedItem]) -> Iterator[GluedItem]:
    """Glue labels to items."""
    labels = set()
    section = "any"
    for item in items:
        if isinstance(item, ParsedLabel):
            labels.add(item.name)
        elif isinstance(item, ParsedDirective) and item.name == (".sec"):
            if not (item.value and item.value.type == "raw_value" and isinstance(item.value.value, str)):
                raise AssemblyError("section name '{}' with type {} was invalid on line {}".format(
                    item.value.value if item.value else None, item.value.type if item.value else None, item.line))
            section = item.value.value
        else:
            yield item.__class__(labels=labels, value=item.value, name=item.name, section=section, line=item.line)
            labels = set()


@force_resolved
def assign_vectors(items: Iterable[GluedItem]) -> Iterator[Union[GluedItem, UnresolvedAddressValue]]:
    """Assign vectors from directives."""
    for item in items:
        if isinstance(item, ParsedDirective) and item.name.startswith(".vec"):
            vector_name = item.name[5:]
            assert vector_name in VECTORS and item.value and item.value.type == "reference" and isinstance(
                item.value.value, str)
            yield UnresolvedAddressValue(instruction=Instruction.JUMP,
                                         data=item.value.value,
                                         address=VECTORS[vector_name].address)
        else:
            yield item


def get_section_sizes(items: Iterable[Union[GluedItem, UnresolvedAddressValue]]) -> Dict[str, int]:
    """Get section names and sizes."""
    sections: Dict[str, int] = {}
    for item in items:
        if isinstance(item, UnresolvedAddressValue):
            continue
        if item.section not in sections:
            sections[item.section] = 0
        sections[item.section] += 1
    return sections


def assign_sections(region_table: RegionTable, sections: Dict[str, int]):
    """Assign memory sections.
    
    This is a packing problem and therefore reasonably complex.
    A simplistic algorithm is used here which may not always be optimal if user
    assigned addresses are used for some sections.
    """
    used_space: Set[Tuple[int, int]] = set()

    def in_used_space(start, end):
        return start > 0xfff or end > 0xfff or any(
            map(lambda x: (start >= x[0] and start <= x[1]) or (end >= x[0] and end <= x[1]), used_space))

    def find_free_space(size):
        for _, end in used_space:
            start_to_try = end + 1
            end_to_try = end + size
            if not in_used_space(start_to_try, end_to_try):
                return start_to_try, end_to_try
        raise AssemblyError("ran out of free space")

    for name, item in region_table.items():
        if in_used_space(item.start, item.end):
            raise AssemblyError("region {} assigned in used space, memory is likely full".format(name))
        used_space.add((item.start, item.end))

    for section_name, section_size in sections.items():
        section_start, section_end = find_free_space(section_size)
        used_space.add((section_start, section_end))
        region_table[section_name] = Region(type="user", start=section_start, end=section_end, count=0)


def get_address(region_table: RegionTable, item: GluedItem) -> int:
    """Get an address for a value. Mutates region_table."""
    if item.section not in region_table:
        raise AssemblyError("item from line {} has section {} which is not in region table, this is a bug".format(
            item.line, item.section))

    # Assign address to next empty slot in section
    address = region_table[item.section].start + region_table[item.section].count

    # Increase section use count
    region_table[item.section].count += 1

    # Check to ensure section is of correct size still
    if region_table[item.section].start + region_table[item.section].count - 1 > region_table[item.section].end:
        raise AssemblyError("item from line {} did not fit in section {}, this is a bug".format(
            item.line, item.section))

    return address


def transform_character(to_transform: str) -> int:
    """Transform a character to small encoding."""
    x = ord(to_transform[0])

    if x >= ord("A") and x <= ord("Z"):
        return (x - ord("A")) & 0x3f

    if x >= ord("a") and x <= ord("z"):
        return (x + 26 - ord('a')) & 0x3f

    if x >= ord("0") and x <= ord("9"):
        return (x + 52 - ord("0")) & 0x3f

    if x == ord(" "):
        return 62

    if x == ord("_"):
        return 63

    raise AssemblyError("character '{}' cannot be encoded in small encoding".format(to_transform))


def serialise_value(value: Optional[ParsedValue]) -> Union[int, str]:
    """Serialise abstract values into raw integer values, preserving references as strings."""
    # No value is the same as a zero
    if not value:
        return 0

    # References are just passed out as a string
    if value.type == "reference":
        return value.value

    # Integers are just passed out as they are
    if value.type == "integer":
        return value.value

    # Short strings are transformed and packed
    if value.type == "short_string":
        if not isinstance(value.value, str):
            raise AssemblyError("value of short string was not a string, this is a bug")
        return (transform_character(value.value[0]) << 6) | transform_character(value.value[1])

    # ASCII strings are packed
    if value.type == "ascii_string":
        if not isinstance(value.value, str):
            raise AssemblyError("value of short string was not a string, this is a bug")
        return ((ord(value.value[1]) << 8) & 0xff00) | (ord(value.value[0]) & 0x00ff)

    # Short characters are transformed and padded
    if value.type == "short_character":
        if not isinstance(value.value, str):
            raise AssemblyError("value of short string was not a string, this is a bug")
        return (transform_character("_") << 6) | transform_character(value.value[0])

    # ASCII characters are transformed
    if value.type == "ascii_character":
        if not isinstance(value.value, str):
            raise AssemblyError("value of short string was not a string, this is a bug")
        return ord(value.value[0]) & 0x00ff

    raise AssemblyError("unknown value to type to serialise {}, this is a bug".format(value.type))


@force_resolved
def assign_constants(
    reference_table: ReferenceTable, region_table: RegionTable, items: Iterable[Union[GluedItem,
                                                                                      UnresolvedAddressValue]]
) -> Iterator[Union[GluedItem, UnresolvedAddressValue, UnresolvedAddressConstant, AddressValue]]:
    """Assign addresses to constants. Mutates region_table and reference_table."""
    for item in items:
        # If the item is a directive
        if isinstance(item, ParsedDirective) and item.name == ".const":
            # Assign the instruction address
            address = get_address(region_table, item)

            # Add labels associated with this instruction to the reference
            # table now that we have an address
            for label in item.labels:
                reference_table[label] = address

            # Load the constant value
            value = serialise_value(item.value)

            # If value is an unresolved reference
            if isinstance(value, str):
                # Create an unresolved constant
                yield UnresolvedAddressConstant(address=address, value=value)

            # If value is an integer
            elif isinstance(value, int):
                # Simply store it
                yield AddressValue(address=address, value=value)

        # If not a directive, passthrough
        else:
            yield item


@force_resolved
def assign_instructions(
    reference_table: ReferenceTable, region_table: RegionTable,
    items: Iterable[Union[GluedItem, AddressValue, UnresolvedAddressValue, UnresolvedAddressConstant]]
) -> Iterator[Union[UnresolvedAddressValue, AddressValue, UnresolvedAddressConstant]]:
    """Assign addresses to instructions. Mutates region_table and reference_table."""
    for item in items:
        # If the item is an instruction
        if isinstance(item, ParsedInstruction):
            # Assign the instruction an address
            address = get_address(region_table, item)

            # Add labels associated with this instruction to the reference
            # table now that we have an address
            for label in item.labels:
                reference_table[label] = address

            # Load the raw value for the instruction's data portion
            value = serialise_value(item.value)

            # Try and get the instruction's opcode
            try:
                instruction = Instruction[item.name.upper()]
            except KeyError:
                raise AssemblyError("unknown instruction {} on line {}".format(item.name, item.line))

            # If we got a string back, it's a reference
            if isinstance(value, str):
                # Create an unresolved address value to be resolved later
                yield UnresolvedAddressValue(address=address, instruction=instruction, data=value)

            # If we got an integer back it's a raw value
            elif isinstance(value, int):
                value = ((instruction << 12) & 0xf000) | (value & 0x0fff)
                yield AddressValue(address=address, value=value)

            # If it is neither someting has gone very wrong
            else:
                raise AssemblyError("error value {} on line {}".format(value, item.line))

        # If we still have a directive at this point, we have no idea what it is
        elif isinstance(item, ParsedDirective):
            raise AssemblyError("unknown directive {} on line {}".format(item.name, item.line))

        # If it's already a value, we just pass it through
        else:
            yield item


def resolve_references(
    reference_table: ReferenceTable, items: Iterable[Union[UnresolvedAddressValue, UnresolvedAddressConstant,
                                                           AddressValue]]
) -> Iterator[AddressValue]:
    """Resolve references in address values."""
    for item in items:
        # If the item is already resolved, let it pass through
        if isinstance(item, AddressValue):
            yield item
            continue

        # If the item is unresolved, resolve it
        yield item.resolve(reference_table)


def serialise_to_text_file(reference_table: ReferenceTable, region_table: RegionTable,
                           resolved_items: Iterable[AddressValue]) -> bytes:
    """Serialise to a memory file."""
    lines = []

    lines.append("/* GENERATED from sma16asm.py")
    lines.append(" *")
    lines.append(" * Regions:")
    for region_name, region_properties in sorted(region_table.items(), key=lambda x: x[1].start):
        lines.append(" *   - {} from 0x{:03x} to 0x{:03x}".format(region_name, region_properties.start,
                                                                  region_properties.end))
    lines.append(" */")

    lines.append("START_PROGRAM")
    for item in resolved_items:
        lines.append("MEM(0x{:03x}, 0x{:x}, 0x{:03x})".format(item.address, (item.value >> 12) & 0xf,
                                                              item.value & 0xfff))
    lines.append("END_PROGRAM")

    return "\n".join(lines).encode("ascii")


def serialise_to_bin_file(resolved_items: Iterable[AddressValue]) -> bytes:
    """Serialise to a memory image file."""
    resolved_items = list(resolved_items)

    memory: Dict[int, int] = {key: 0 for key in range(max(map(lambda x: x.address, resolved_items)))}

    for item in resolved_items:
        memory[item.address] = item.value

    memory_bytes = b""
    for _, value in memory.items():
        memory_bytes += struct_pack(">H", value)

    return memory_bytes


def serialise_to_hex_file(resolved_items: Iterable[AddressValue]) -> bytes:
    """Serialise to a hex file."""
    resolved_items = list(resolved_items)

    memory: Dict[int, int] = {key: 0 for key in range(max(map(lambda x: x.address, resolved_items)))}

    for item in resolved_items:
        memory[item.address] = item.value

    memory_bytes = b""
    for address, value in memory.items():
        memory_bytes += "{:04x}".format(value).encode("ascii")
        if address % 8 == 7:
            memory_bytes += b"\n"

    return memory_bytes


def assemble_file(file_path: str, output_file: str, output_format: str = "text"):
    """Assemble a file."""
    parsed_lines = parse_lines(file_path)

    glued_items = glue_labels_and_sections(parsed_lines)

    reference_table: ReferenceTable = {}
    reference_table.update(CONSTANTS)

    region_table: RegionTable = {}
    region_table.update(REGIONS)

    items_with_vectors_assigned = assign_vectors(glued_items)

    sections = get_section_sizes(items_with_vectors_assigned)
    if sum(sections.values()) >= 2**12 - 16:
        raise AssemblyError("memory full")

    assign_sections(region_table, sections)

    partially_unresolved_items = assign_constants(reference_table, region_table, items_with_vectors_assigned)
    unresolved_items = assign_instructions(reference_table, region_table, partially_unresolved_items)
    resolved_items = resolve_references(reference_table, unresolved_items)

    if output_format == "bin":
        output_bytes = serialise_to_bin_file(resolved_items)
    elif output_format == "hex":
        output_bytes = serialise_to_hex_file(resolved_items)
    else:
        output_bytes = serialise_to_text_file(reference_table, region_table, resolved_items)

    with open(output_file, "wb") as output_handle:
        output_handle.write(output_bytes)


def main() -> int:
    """Entry point function."""
    argument_parser = ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter)

    argument_parser.add_argument("INPUT")
    argument_parser.add_argument("-o", "--output", default="a.txt")
    argument_parser.add_argument("-f",
                                 "--format",
                                 default="auto",
                                 choices=("auto", "text", "t", "bin", "b", "hex", "h", "x"))

    parsed_arguments = argument_parser.parse_args()

    output_path = path.abspath(parsed_arguments.output)

    output_format = parsed_arguments.format
    if output_format == "auto":
        _, ext = path.splitext(output_path)
        if ext == ".bin":
            output_format = "bin"
        elif ext == ".hex":
            output_format = "hex"
        else:
            output_format = "text"
    elif output_format == "b":
        output_format = "bin"
    elif output_format == "h" or output_format == "x":
        output_format = "hex"
    elif output_format == "t":
        output_format = "text"

    if not path.isdir(path.dirname(output_path)):
        print("Output directory does not exist.")
        return 2

    input_file = path.abspath(parsed_arguments.INPUT)

    if not path.isfile(input_file):
        print("Input file does not exist.")
        return 3

    try:
        assemble_file(input_file, output_file=output_path, output_format=output_format)
    except AssemblyError as error:
        print("Assembly failed: {}.".format(error), file=stderr)
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
