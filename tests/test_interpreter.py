"""Тесты интерпретатора и его работы вместе с ассемблером."""

import argparse
import contextlib
import csv
import io
import random
import tempfile
import unittest
from pathlib import Path

import interpreter
from assembler import assemble, parse_program
from interpreter import Memory, VmError, parse_range, run
from isa import ADDRESS_SPACE, Instruction, decode, encode
from tests import ROOT


def build(text):
    """Ассемблирует текст программы в байты."""
    return b"".join(assemble(parse_program(text)))


def run_file(name):
    """Выполняет программу из каталога programs."""
    text = (ROOT / "programs" / name).read_text(encoding="utf-8")
    return run(build(text))


def cells(memory, first, count):
    """Возвращает значения count ячеек начиная с first."""
    return [memory.read(first + index) for index in range(count)]


class DecodeTest(unittest.TestCase):
    """Проверки обратного преобразования машинного кода."""

    def test_random_commands_survive_round_trip(self):
        rng = random.Random(3)
        for _ in range(1000):
            opcode = rng.choice((2, 9, 6))
            item = Instruction(
                opcode,
                rng.randrange(ADDRESS_SPACE),
                rng.randrange(ADDRESS_SPACE),
            )
            self.assertEqual(decode(encode(item)), item)

    def test_random_load_commands_survive_round_trip(self):
        rng = random.Random(4)
        for _ in range(1000):
            item = Instruction(
                15, rng.randrange(ADDRESS_SPACE), rng.randrange(1024)
            )
            self.assertEqual(decode(encode(item)), item)


class MemoryTest(unittest.TestCase):
    """Проверки модели памяти."""

    def test_unwritten_cell_is_zero(self):
        self.assertEqual(Memory().read(ADDRESS_SPACE - 1), 0)

    def test_address_outside_memory_is_rejected(self):
        with self.assertRaises(VmError):
            Memory().read(ADDRESS_SPACE)


class RunTest(unittest.TestCase):
    """Проверки выполнения команд."""

    def test_load_writes_constant(self):
        memory = run(build("op,b,c\nload,500,1023\n"))
        self.assertEqual(memory.read(500), 1023)

    def test_read_and_write_copy_value(self):
        for mnemonic in ("read", "write"):
            text = f"op,b,c\nload,500,7\n{mnemonic},500,600\n"
            with self.subTest(mnemonic):
                self.assertEqual(run(build(text)).read(600), 7)

    def test_copy_array_program(self):
        memory = run_file("copy_array.csv")
        source = [11, 22, 33, 44, 1023]
        self.assertEqual(cells(memory, 200, 5), source)
        self.assertEqual(cells(memory, 300, 5), source)
        self.assertEqual(cells(memory, 400, 5), source)

    def test_program_is_stored_in_common_memory(self):
        program = build("op,b,c\nload,500,7\n")
        memory = run(program)
        self.assertEqual(bytes(cells(memory, 0, len(program))), program)

    def test_program_can_change_its_next_command(self):
        text = "op,b,c\nload,10,4\nload,500,7\n"
        self.assertEqual(run(build(text)).read(500), 1)

    def test_broken_programs_are_rejected(self):
        broken = {
            "неизвестный код": b"\x00" * 8,
            "обрезанная команда": build("op,b,c\nread,1,2\n")[:-1],
        }
        for name, program in broken.items():
            with self.subTest(name), self.assertRaises(VmError):
                run(program)

    def test_command_cell_must_hold_byte(self):
        program = build("op,b,c\nload,7,1023\nload,500,7\n")
        with self.assertRaises(VmError):
            run(program)


class CommandLineTest(unittest.TestCase):
    """Проверки запуска интерпретатора из командной строки."""

    def test_dump_contains_requested_range(self):
        with tempfile.TemporaryDirectory() as folder:
            binary = Path(folder) / "prog.bin"
            dump = Path(folder) / "dump.csv"
            binary.write_bytes(build("op,b,c\nload,500,7\n"))
            code = interpreter.main([str(binary), str(dump), "499-500"])
            with dump.open(encoding="utf-8", newline="") as file:
                rows = list(csv.reader(file))
        self.assertEqual(code, 0)
        expected = [["address", "value"], ["499", "0"], ["500", "7"]]
        self.assertEqual(rows, expected)

    def test_missing_program_gives_error_code(self):
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            code = interpreter.main(["no_such.bin", "dump.csv", "0-1"])
        self.assertEqual(code, 1)

    def test_bad_ranges_are_rejected(self):
        for text in ("abc", "5", "5-1", f"0-{ADDRESS_SPACE}"):
            with self.subTest(text):
                with self.assertRaises(argparse.ArgumentTypeError):
                    parse_range(text)
