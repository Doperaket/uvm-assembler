"""Ассемблер УВМ: переводит программу из CSV в машинный код."""

import argparse
import csv
import io
import sys
from pathlib import Path

from isa import ADDRESS_BITS, BY_MNEMONIC, Instruction, encode

HEADER = ["op", "b", "c"]


class AssemblerError(Exception):
    """Ошибка в тексте программы на языке ассемблера."""


def parse_number(text, bits, name, line):
    """Разбирает число поля и проверяет, что оно помещается в bits бит."""
    try:
        value = int(text, 0)
    except ValueError:
        message = f"строка {line}: {name} не является числом: {text!r}"
        raise AssemblerError(message) from None
    if value not in range(1 << bits):
        message = f"строка {line}: {name}={value} не помещается в {bits} бит"
        raise AssemblerError(message)
    return value


def parse_row(row, line):
    """Переводит одну строку CSV в команду."""
    if len(row) != len(HEADER):
        message = f"строка {line}: ожидается {len(HEADER)} поля"
        raise AssemblerError(message)
    mnemonic, b_text, c_text = row
    fmt = BY_MNEMONIC.get(mnemonic)
    if fmt is None:
        raise AssemblerError(f"строка {line}: неизвестная команда {mnemonic!r}")
    b_value = parse_number(b_text, ADDRESS_BITS, "B", line)
    c_value = parse_number(c_text, fmt.c_bits, "C", line)
    return Instruction(fmt.opcode, b_value, c_value)


def parse_program(text):
    """Переводит текст программы в список команд."""
    reader = csv.reader(io.StringIO(text))
    header = [field.strip() for field in next(reader, [])]
    if header != HEADER:
        raise AssemblerError("строка 1: ожидается заголовок op,b,c")
    program = []
    for row in reader:
        fields = [field.strip() for field in row]
        if any(fields):
            program.append(parse_row(fields, reader.line_num))
    return program


def format_bytes(code):
    """Возвращает машинный код команды в виде из спецификации."""
    return ", ".join(f"0x{byte:02X}" for byte in code)


def assemble(program):
    """Переводит промежуточное представление в машинный код команд."""
    return [encode(instruction) for instruction in program]


def parse_args(argv):
    """Разбирает аргументы командной строки."""
    parser = argparse.ArgumentParser(description="Ассемблер УВМ")
    parser.add_argument("source", help="файл с текстом программы (CSV)")
    parser.add_argument("output", help="двоичный файл-результат")
    parser.add_argument(
        "--test", action="store_true", help="режим тестирования"
    )
    return parser.parse_args(argv)


def main(argv=None):
    """Точка входа: возвращает код завершения процесса."""
    args = parse_args(argv)
    try:
        text = Path(args.source).read_text(encoding="utf-8-sig")
        codes = assemble(parse_program(text))
        Path(args.output).write_bytes(b"".join(codes))
    except (OSError, AssemblerError) as error:
        print(f"Ошибка: {error}", file=sys.stderr)
        return 1
    if args.test:
        for code in codes:
            print(format_bytes(code))
    print(f"Ассемблировано команд: {len(codes)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
