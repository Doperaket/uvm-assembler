"""Тесты формирования машинного кода и CLI ассемблера."""

import contextlib
import io
import tempfile
import unittest
from pathlib import Path

from assembler import assemble, format_bytes, main, parse_program
from isa import Instruction, encode
from tests import ROOT

SPEC_PROGRAM = ROOT / "programs" / "spec.csv"
SPEC_CODES = [
    "0x5F, 0x08, 0x00, 0x00, 0x18, 0x06",
    "0x22, 0x1B, 0x00, 0x00, 0x90, 0x00, 0x00, 0x00",
    "0xB9, 0x34, 0x00, 0x00, 0xDC, 0x0A, 0x00, 0x00",
    "0xE6, 0x0B, 0x00, 0x00, 0x84, 0x09, 0x00, 0x00",
]


class EncodeTest(unittest.TestCase):
    """Проверки кодирования на тестах из спецификации."""

    def test_spec_program_gives_spec_bytes(self):
        text = SPEC_PROGRAM.read_text(encoding="utf-8")
        codes = assemble(parse_program(text))
        self.assertEqual([format_bytes(code) for code in codes], SPEC_CODES)

    def test_command_sizes(self):
        self.assertEqual(len(encode(Instruction(15, 1, 2))), 6)
        for opcode in (2, 9, 6):
            self.assertEqual(len(encode(Instruction(opcode, 1, 2))), 8)

    def test_maximum_fields_fit_into_command(self):
        max_address = (1 << 30) - 1
        code = encode(Instruction(2, max_address, max_address))
        self.assertEqual(code, b"\xf2" + b"\xff" * 7)


class CommandLineTest(unittest.TestCase):
    """Проверки запуска ассемблера из командной строки."""

    def run_main(self, *args):
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            code = main(list(args))
        return code, stdout.getvalue().splitlines()

    def test_test_mode_prints_bytes_and_count(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "spec.bin"
            code, lines = self.run_main(
                str(SPEC_PROGRAM), str(target), "--test"
            )
            size = target.stat().st_size
        self.assertEqual(code, 0)
        self.assertEqual(lines, [*SPEC_CODES, "Ассемблировано команд: 4"])
        self.assertEqual(size, 6 + 8 * 3)

    def test_normal_mode_prints_only_count(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "spec.bin"
            _, lines = self.run_main(str(SPEC_PROGRAM), str(target))
        self.assertEqual(lines, ["Ассемблировано команд: 4"])

    def test_missing_file_gives_error_code(self):
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            code = main(["no_such_file.csv", "unused.bin"])
        self.assertEqual(code, 1)
