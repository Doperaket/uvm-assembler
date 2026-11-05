"""Интерпретатор УВМ: выполняет программу и сохраняет дамп памяти."""

import argparse
import csv
import sys
from pathlib import Path

from isa import ADDRESS_SPACE, BY_MNEMONIC, BY_OPCODE, OPCODE_MASK, decode

BYTE_RANGE = range(1 << 8)
OP_LOAD = BY_MNEMONIC["load"].opcode
OP_READ = BY_MNEMONIC["read"].opcode
OP_WRITE = BY_MNEMONIC["write"].opcode


class VmError(Exception):
    """Ошибка при выполнении программы."""


class Memory:
    """Объединённая память команд и данных с разреженным хранением ячеек."""

    def __init__(self):
        self._cells = {}

    def read(self, address):
        """Возвращает значение ячейки, незаписанные ячейки равны нулю."""
        self._check(address)
        return self._cells.get(address, 0)

    def write(self, address, value):
        """Записывает значение в ячейку."""
        self._check(address)
        self._cells[address] = value

    def load_program(self, program):
        """Размещает байты программы в ячейках начиная с адреса 0."""
        for address, byte in enumerate(program):
            self.write(address, byte)

    @staticmethod
    def _check(address):
        if address not in range(ADDRESS_SPACE):
            raise VmError(f"адрес {address} вне памяти")


def execute_load(memory, instruction):
    """Загрузка константы: mem[B] = C."""
    memory.write(instruction.b, instruction.c)


def execute_copy(memory, instruction):
    """Чтение и запись значения: mem[C] = mem[B]."""
    memory.write(instruction.c, memory.read(instruction.b))


EXECUTORS = {
    OP_LOAD: execute_load,
    OP_READ: execute_copy,
    OP_WRITE: execute_copy,
}


def fetch(memory, counter, end):
    """Читает из памяти машинный код команды по адресу counter."""
    fmt = BY_OPCODE.get(memory.read(counter) & OPCODE_MASK)
    if fmt is None or fmt.opcode not in EXECUTORS:
        raise VmError(f"адрес {counter}: неизвестная команда")
    if counter + fmt.size > end:
        raise VmError(f"адрес {counter}: команда обрезана")
    code = [memory.read(counter + i) for i in range(fmt.size)]
    if any(value not in BYTE_RANGE for value in code):
        raise VmError(f"адрес {counter}: ячейка команды не является байтом")
    return bytes(code)


def run(program):
    """Выполняет программу до её конца и возвращает память."""
    memory = Memory()
    memory.load_program(program)
    counter = 0
    while counter < len(program):
        code = fetch(memory, counter, len(program))
        instruction = decode(code)
        EXECUTORS[instruction.a](memory, instruction)
        counter += len(code)
    return memory


def write_dump(memory, path, first, last):
    """Сохраняет ячейки с first по last включительно в CSV."""
    with Path(path).open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file, lineterminator="\n")
        writer.writerow(["address", "value"])
        for address in range(first, last + 1):
            writer.writerow([address, memory.read(address)])


def parse_range(text):
    """Разбирает диапазон адресов дампа вида START-END."""
    first_text, _, last_text = text.partition("-")
    try:
        first, last = int(first_text, 0), int(last_text, 0)
    except ValueError:
        message = f"диапазон должен иметь вид START-END: {text!r}"
        raise argparse.ArgumentTypeError(message) from None
    if first > last or last not in range(ADDRESS_SPACE):
        raise argparse.ArgumentTypeError(f"неверный диапазон: {text!r}")
    return first, last


def parse_args(argv):
    """Разбирает аргументы командной строки."""
    parser = argparse.ArgumentParser(description="Интерпретатор УВМ")
    parser.add_argument("program", help="двоичный файл с программой")
    parser.add_argument("dump", help="файл для дампа памяти (CSV)")
    parser.add_argument(
        "range", type=parse_range, help="диапазон адресов START-END"
    )
    return parser.parse_args(argv)


def main(argv=None):
    """Точка входа: возвращает код завершения процесса."""
    args = parse_args(argv)
    first, last = args.range
    try:
        memory = run(Path(args.program).read_bytes())
        write_dump(memory, args.dump, first, last)
    except (OSError, VmError) as error:
        print(f"Ошибка: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
