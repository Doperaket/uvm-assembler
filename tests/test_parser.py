"""Тесты разбора языка ассемблера."""

import unittest

from assembler import AssemblerError, parse_program
from isa import Instruction
from tests import ROOT

SPEC_FIELDS = [
    Instruction(15, 133, 390),
    Instruction(2, 434, 36),
    Instruction(9, 843, 695),
    Instruction(6, 190, 609),
]
SPEC_PROGRAM = ROOT / "programs" / "spec.csv"


class ParseProgramTest(unittest.TestCase):
    """Проверки перевода текста в промежуточное представление."""

    def test_spec_program_gives_spec_fields(self):
        text = SPEC_PROGRAM.read_text(encoding="utf-8")
        self.assertEqual(parse_program(text), SPEC_FIELDS)

    def test_blank_lines_and_spaces_are_ignored(self):
        text = "op, b, c\n\nload, 1, 2\n   \n"
        self.assertEqual(parse_program(text), [Instruction(15, 1, 2)])

    def test_hex_numbers_are_accepted(self):
        text = "op,b,c\nread,0x10,0x20\n"
        self.assertEqual(parse_program(text), [Instruction(2, 16, 32)])

    def test_field_limits(self):
        max_address = (1 << 30) - 1
        text = f"op,b,c\nload,{max_address},1023\n"
        self.assertEqual(
            parse_program(text), [Instruction(15, max_address, 1023)]
        )

    def test_bad_programs_are_rejected(self):
        bad_programs = {
            "нет заголовка": "load,1,2\n",
            "пустой файл": "",
            "неизвестная команда": "op,b,c\njump,1,2\n",
            "мало полей": "op,b,c\nload,1\n",
            "много полей": "op,b,c\nload,1,2,3\n",
            "не число": "op,b,c\nload,x,2\n",
            "отрицательное": "op,b,c\nload,-1,2\n",
            "большая константа": "op,b,c\nload,1,1024\n",
            "большой адрес": f"op,b,c\nread,{1 << 30},2\n",
        }
        for name, text in bad_programs.items():
            with self.subTest(name), self.assertRaises(AssemblerError):
                parse_program(text)

    def test_error_names_the_line(self):
        with self.assertRaisesRegex(AssemblerError, "строка 3"):
            parse_program("op,b,c\nload,1,2\njump,1,2\n")
