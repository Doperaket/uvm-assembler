"""Сквозные тесты программ этапа 5: ассемблер, интерпретатор и дамп."""

import contextlib
import csv
import io
import tempfile
import unittest
from pathlib import Path

import assembler
import interpreter
from tests import ROOT

PROGRAMS = ROOT / "programs"
EXPECTED_DUMPS = {
    "sqrt_vector": ("300-304", [4, 5, 9, 12, 31]),
    "example_squares": ("300-304", [1, 2, 3, 20, 31]),
    "example_rounding": ("300-304", [0, 1, 3, 9, 31]),
    "example_chain": ("200-204", [256, 16, 4, 2, 1]),
}


def dump_program(name, address_range):
    """Запускает программу через оба CLI и возвращает значения из дампа."""
    with tempfile.TemporaryDirectory() as folder:
        binary = Path(folder) / f"{name}.bin"
        dump = Path(folder) / f"{name}.csv"
        with contextlib.redirect_stdout(io.StringIO()):
            assembler.main([str(PROGRAMS / f"{name}.csv"), str(binary)])
        interpreter.main([str(binary), str(dump), address_range])
        with dump.open(encoding="utf-8", newline="") as file:
            return [int(row["value"]) for row in csv.DictReader(file)]


class ProgramsTest(unittest.TestCase):
    """Проверка дампов тестовой задачи и примеров."""

    def test_dumps_match_expected_values(self):
        for name, (address_range, expected) in EXPECTED_DUMPS.items():
            with self.subTest(name):
                self.assertEqual(dump_program(name, address_range), expected)

    def test_source_vector_stays_unchanged(self):
        self.assertEqual(
            dump_program("sqrt_vector", "200-204"), [16, 25, 81, 144, 1000]
        )
