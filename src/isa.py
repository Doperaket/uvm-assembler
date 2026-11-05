"""Спецификация УВМ варианта №3: форматы команд и их поля."""

from dataclasses import dataclass

ADDRESS_BITS = 30
ADDRESS_SPACE = 1 << ADDRESS_BITS
OPCODE_MASK = 0xF
FIELD_B_SHIFT = 4
FIELD_C_SHIFT = 34


@dataclass(frozen=True)
class CommandFormat:
    """Формат команды: мнемоника, код A, размер и ширина поля C."""

    mnemonic: str
    opcode: int
    size: int
    c_bits: int


FORMATS = (
    CommandFormat("load", 15, 6, 10),
    CommandFormat("read", 2, 8, ADDRESS_BITS),
    CommandFormat("write", 9, 8, ADDRESS_BITS),
    CommandFormat("sqrt", 6, 8, ADDRESS_BITS),
)
BY_MNEMONIC = {fmt.mnemonic: fmt for fmt in FORMATS}
BY_OPCODE = {fmt.opcode: fmt for fmt in FORMATS}


@dataclass(frozen=True)
class Instruction:
    """Команда в промежуточном представлении: поля A, B и C."""

    a: int
    b: int
    c: int


def encode(instruction):
    """Переводит команду в машинный код с порядком байт little-endian."""
    fmt = BY_OPCODE[instruction.a]
    word = (
        instruction.a
        | instruction.b << FIELD_B_SHIFT
        | instruction.c << FIELD_C_SHIFT
    )
    return word.to_bytes(fmt.size, "little")


def decode(code):
    """Переводит машинный код команды в промежуточное представление."""
    word = int.from_bytes(code, "little")
    opcode = word & OPCODE_MASK
    fmt = BY_OPCODE[opcode]
    b_value = (word >> FIELD_B_SHIFT) & (ADDRESS_SPACE - 1)
    c_value = (word >> FIELD_C_SHIFT) & ((1 << fmt.c_bits) - 1)
    return Instruction(opcode, b_value, c_value)
