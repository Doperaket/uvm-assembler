"""Спецификация УВМ варианта №3: форматы команд и их поля."""

from dataclasses import dataclass

ADDRESS_BITS = 30
ADDRESS_SPACE = 1 << ADDRESS_BITS


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
