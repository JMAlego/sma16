#!/usr/bin/env python3
import sys
import re

class Colour:
    RESET = u"\u001B[0m"
    BLACK = u"\u001B[30m"
    RED = u"\u001B[31m"
    GREEN = u"\u001B[32m"
    YELLOW = u"\u001B[33m"
    BLUE = u"\u001B[34m"
    PURPLE = u"\u001B[35m"
    CYAN = u"\u001B[36m"
    WHITE = u"\u001B[37m"
    BOLD = u"\u001b[1m"
    UNDERLINED = u"\u001b[4m"
    REVERSED = u"\u001b[7m"

    @staticmethod
    def reset(string):
        return Colour.RESET + str(string) + Colour.RESET

    @staticmethod
    def black(string):
        return Colour.BLACK + str(string) + Colour.RESET

    @staticmethod
    def red(string):
        return Colour.RED + str(string) + Colour.RESET

    @staticmethod
    def green(string):
        return Colour.GREEN + str(string) + Colour.RESET

    @staticmethod
    def yellow(string):
        return Colour.YELLOW + str(string) + Colour.RESET

    @staticmethod
    def blue(string):
        return Colour.BLUE + str(string) + Colour.RESET

    @staticmethod
    def purple(string):
        return Colour.PURPLE + str(string) + Colour.RESET

    @staticmethod
    def cyan(string):
        return Colour.CYAN + str(string) + Colour.RESET

    @staticmethod
    def white(string):
        return Colour.WHITE + str(string) + Colour.RESET

    @staticmethod
    def bold(string):
        return Colour.BOLD + str(string) + Colour.RESET

    @staticmethod
    def underlined(string):
        return Colour.UNDERLINED + str(string) + Colour.RESET

    @staticmethod
    def reversed(string):
        return Colour.REVERSED + str(string) + Colour.RESET

RE_LET = re.compile(r"^let +(?P<vars>(?:[a-z]+ *, *)*[a-z]+) *: *(?P<type>word|byte|dword|qword|string|address)$", re.IGNORECASE)

RE_ASSIGNMENT = re.compile(r"^(?P<var>[a-z]+) *= *(?P<value>.+?)$", re.IGNORECASE)

RE_LABEL = re.compile(r"^label (?P<name>@[a-z]+)$", re.IGNORECASE)
RE_GOTO = re.compile(r"^goto (?P<name>@[a-z]+)$", re.IGNORECASE)

RE_IF = re.compile(r"^if +(?P<condition>.+) +then$", re.IGNORECASE)
RE_ELSE = re.compile(r"^else$", re.IGNORECASE)
RE_END_IF = re.compile(r"^end +if$", re.IGNORECASE)

RE_FUNC = re.compile(r"^func +(?P<name>(?:[a-z]+))(?:\( *(?P<vars>(?:[a-z]+ *, *)*[a-z]+) *\)|\( *\)) +is$", re.IGNORECASE)
RE_END_FUNC = re.compile(r"^end +func$", re.IGNORECASE)

RE_WHILE = re.compile(r"^while +(?P<condition>.+) +do$", re.IGNORECASE)
RE_END_WHILE = re.compile(r"^end +while$", re.IGNORECASE)

RE_FOR = re.compile(r"^for +(?P<name>(?:[a-z]+)) +from +(?P<start>.+) +to +(?P<end>.+) +do$", re.IGNORECASE)
RE_END_FOR = re.compile(r"^end +for$", re.IGNORECASE)

RE_MACRO = re.compile(r"^% *(?P<macro>.+)$")

RE_INLINE_START = re.compile(r"^inline begin$", re.IGNORECASE)
RE_INLINE_END = re.compile(r"^inline end$", re.IGNORECASE)

RE_OPERATORS = re.compile(r"(?P<var1>[a-z]+) *(?P<operator>\+|\-|\*|\/|\^|\&|\|) *(?P<var2>[a-z]+)", re.IGNORECASE)
RE_FUNCTION = re.compile(r"(?P<func>[a-z]+)\((?P<vars>(?: *[a-z]+ *)?(?:, *[a-z]+ *)*)\)", re.IGNORECASE)

RE_COMMENT = re.compile(r"^(?P<code>.*) *(?P<comment>#.*)$")

KEYWORDS = set([
    "let",
    "label",
    "if",
    "then",
    "else",
    "return",
    "pop",
    "push",
    "string",
    "byte",
    "word",
    "qword",
    "dword",
    "address",
    "goto",
    "halt",
    "inline",
    "begin",
    "end",
    "func",
    "is",
    "for",
    "while",
    "do",
    "from",
    "to"
])

class DefinedName:
    def __init__(self, name, type_string, index, line_number):
        self.name = name
        self.type_string = type_string
        self.index = index
        self.line_number = line_number
        self.internal_name = str(name) + "." + str(self.type_string) + "." + str(line_number)
    def __str__(self):
        return "DefinedName(" + str(self.name) + ", " + str(self.type_string) + ", " + str(self.index) + ", " \
               + str(self.line_number) + ", " + str(self.internal_name) + ")"
    __repr__ = __str__

class ASMLine:
    def __init__(self, instruction=None, data=None, label=None, insert=None, index=None, raw=False):
        self.instruction = instruction
        self.data = data
        self.label = label
        self.insert = insert
        self.index = index
        self.raw = raw 
    def __str__(self):
        return "ASMLine(" + str(self.instruction) + ", " + str(self.data) + ", " + str(self.label) + ", " \
               + str(self.insert) + ", " + str(self.index) + ", " + str(self.raw) + ")"
    __repr__ = __str__

def internal_error(action, message):
    print(Colour.bold(Colour.red("Error")), "while", action, file=sys.stderr)
    print("Internal error:", message, file=sys.stderr)
    print(Colour.bold(Colour.red("\nCompilation halted due to error")), file=sys.stderr)
    sys.exit(2)

def internal_warning(action, message):
    print(Colour.bold(Colour.yellow("Warning")), "while", action, file=sys.stderr)
    print("Internal warning:", message, "\n", file=sys.stderr)

def comp_error(line, line_number, message):
    print(Colour.bold(Colour.red("Error")), "on line", line_number, file=sys.stderr)
    print("Compilation error:", message, file=sys.stderr)
    print('Line: `', line, '`', sep="", file=sys.stderr)
    print(Colour.bold(Colour.red("\nCompilation halted due to error")), file=sys.stderr)
    sys.exit(1)

def comp_warning(line, line_number, message):
    print(Colour.bold(Colour.yellow("Warning")), "on line", line_number, file=sys.stderr)
    print("Compilation warning:", message, file=sys.stderr)
    print('Line: `', line, '`\n', sep="", file=sys.stderr)

def macro(lines):
    return lines

def comp(lines):
    print(Colour.bold(Colour.blue("Compilation started\n")))

    lines = list(enumerate(map(str.strip, lines), 1))
    mapping = {}

    lines = macro(lines)

    defined_names = {}
    for index, (line_number, full_line) in enumerate(lines):
        #Remove comments
        if RE_COMMENT.match(full_line):
            line = RE_COMMENT.match(full_line).group("code").strip()
        else:
            line = full_line
        #Actual Code
        if RE_LET.match(line):
            groups = RE_LET.match(line).groupdict()
            variable_names = map(str.strip, groups["vars"].split(","))
            for name in variable_names:
                if name in KEYWORDS:
                    comp_error(full_line, line_number, "redefinition of keyword `" + str(name) + "` is not allowed")
                elif name in defined_names:
                    comp_error(full_line, line_number, "name already defined on line " + str(defined_names[name].line_number))
                else:
                    defined_names[name] = DefinedName(name, groups["type"], index, line_number)
        elif RE_LABEL.match(line):
            label_name = RE_LABEL.match(line).group("name")
            if label_name in defined_names:
                comp_error(full_line, line_number, "name already defined on line " + str(defined_names[label_name].line_number))
            else:
                defined_names[label_name] = DefinedName(label_name, "label", index, line_number)
                mapping[index] = ASMLine(label=label_name)
    result = []
    for index, asm_line in mapping.items():
        if asm_line.insert is not None and asm_line.index is not None:
            internal_error("finalising assembly", "line had both insert and index directives")
        if asm_line.instruction is None:
            internal_warning("finalising assembly", "line had no instruction")
            asm_line.instruction = "NOOP"
        if asm_line.data is None:
            internal_warning("finalising assembly", "line had no data")
            asm_line.data = 0
        string_line = ""
        if asm_line.insert is not None:
            string_line += ".insert " + hex(asm_line.insert) + " "
        elif asm_line.index is not None:
            string_line += ".index " + hex(asm_line.index) + " "
        if asm_line.label is not None:
            string_line += asm_line.label + " "
        string_line += asm_line.instruction + " "
        string_line += hex(asm_line.data)
        result.append(string_line)
    print(Colour.bold(Colour.green("Compilation finished")))
    return "\n".join(result)

print(Colour.bold("sabl (sma16 abstraction basic language) [v0.1a]"))
print("-----------------------------------------------\n")

if len(sys.argv) == 3:
    with open(sys.argv[1], "r") as fp:
        data = fp.readlines()
    with open(sys.argv[2], "w") as fp:
        fp.write(comp(data))
else:
    print("sabl requires arguments (./sabl.py input_file output_file)")
