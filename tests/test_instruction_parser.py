"""
tests/test_instruction_parser.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Unit tests for the MIPS assembly parser defined in
``src/utils/instruction_parser.py``.

What's tested:
  - ``parse_register`` canonical function (named, numeric, $-prefixed)
  - R-type parsing (add, sub, and, or, sll, move, jr, syscall, nop)
  - I-type parsing (addi, lw/sw, beq/bne, li/la, blez/bgtz)
  - J-type parsing (j, jal)
  - Floating-point parsing (add.s, mul.s)
  - Multi-line program parsing with labels and data sections
  - Error handling for malformed input
"""

from __future__ import annotations

import pytest

from src.utils.instruction import InstructionType
from src.utils.instruction_parser import (
    MIPS_REGISTER_MAP,
    MIPSInstructionParser,
    parse_register,
)

# ========================== parse_register =================================


class TestParseRegister:
    """Canonical register-string → register-number resolver."""

    @pytest.mark.parametrize(
        "reg_str, expected",
        [
            ("$zero", 0),
            ("$t0", 8),
            ("$s0", 16),
            ("$sp", 29),
            ("$ra", 31),
            ("zero", 0),
            ("t0", 8),
            ("a0", 4),
            ("$0", 0),
            ("$8", 8),
            ("$31", 31),
            ("0", 0),
            ("16", 16),
        ],
    )
    def test_known_registers(self, reg_str: str, expected: int) -> None:
        assert parse_register(reg_str) == expected

    def test_unknown_register_defaults_to_zero(self) -> None:
        assert parse_register("$xyz") == 0

    def test_whitespace_is_stripped(self) -> None:
        assert parse_register("  $t0  ") == 8

    def test_out_of_range_numeric_defaults_to_zero(self) -> None:
        assert parse_register("99") == 0


class TestRegisterMap:
    """MIPS_REGISTER_MAP completeness checks."""

    def test_has_32_named_registers(self) -> None:
        assert len(MIPS_REGISTER_MAP) == 32

    def test_zero_through_ra(self) -> None:
        assert MIPS_REGISTER_MAP["zero"] == 0
        assert MIPS_REGISTER_MAP["ra"] == 31


# ========================== Parser Setup ===================================


@pytest.fixture()
def parser() -> MIPSInstructionParser:
    return MIPSInstructionParser()


# ========================== R-type Instructions =============================


class TestRTypeParsing:
    """Standard three-register instructions."""

    def test_add(self, parser: MIPSInstructionParser) -> None:
        inst = parser.parse_instruction("add $t0, $t1, $t2", 0)
        assert inst is not None
        assert inst.opcode == "ADD"
        assert inst.instruction_type == InstructionType.ARITHMETIC
        assert inst.operands == ["$8", "$9", "$10"]
        assert inst.destination == "$8"

    def test_sub(self, parser: MIPSInstructionParser) -> None:
        inst = parser.parse_instruction("sub $s0, $s1, $s2", 4)
        assert inst is not None
        assert inst.opcode == "SUB"
        assert inst.operands == ["$16", "$17", "$18"]

    def test_and(self, parser: MIPSInstructionParser) -> None:
        inst = parser.parse_instruction("and $t0, $t1, $t2", 0)
        assert inst is not None
        assert inst.instruction_type == InstructionType.LOGICAL

    def test_or(self, parser: MIPSInstructionParser) -> None:
        inst = parser.parse_instruction("or $t0, $t1, $t2", 0)
        assert inst is not None
        assert inst.instruction_type == InstructionType.LOGICAL

    def test_slt(self, parser: MIPSInstructionParser) -> None:
        inst = parser.parse_instruction("slt $t0, $t1, $t2", 0)
        assert inst is not None
        assert inst.instruction_type == InstructionType.COMPARISON

    def test_shift_sll(self, parser: MIPSInstructionParser) -> None:
        inst = parser.parse_instruction("sll $t0, $t1, 4", 0)
        assert inst is not None
        assert inst.operands == ["$8", "$9", "4"]
        assert inst.destination == "$8"

    def test_shift_sra(self, parser: MIPSInstructionParser) -> None:
        inst = parser.parse_instruction("sra $t0, $t1, 2", 0)
        assert inst is not None
        assert inst.destination == "$8"


class TestRTypeSpecial:
    """Move, jump-register, syscall, nop."""

    def test_move(self, parser: MIPSInstructionParser) -> None:
        inst = parser.parse_instruction("move $t0, $t1", 0)
        assert inst is not None
        assert inst.opcode == "MOVE"
        assert inst.operands == ["$8", "$9"]
        assert inst.destination == "$8"

    def test_jr(self, parser: MIPSInstructionParser) -> None:
        inst = parser.parse_instruction("jr $ra", 0)
        assert inst is not None
        assert inst.opcode == "JR"
        assert inst.instruction_type == InstructionType.JUMP

    def test_syscall(self, parser: MIPSInstructionParser) -> None:
        inst = parser.parse_instruction("syscall", 0)
        assert inst is not None
        assert inst.instruction_type == InstructionType.SYSTEM

    def test_nop(self, parser: MIPSInstructionParser) -> None:
        inst = parser.parse_instruction("nop", 0)
        assert inst is not None
        assert inst.instruction_type == InstructionType.NOP
        assert inst.operands == []


# ========================== I-type Instructions =============================


class TestITypeParsing:
    """Immediate and memory instructions."""

    def test_addi(self, parser: MIPSInstructionParser) -> None:
        inst = parser.parse_instruction("addi $t0, $t1, 42", 0)
        assert inst is not None
        assert inst.opcode == "ADDI"
        assert inst.operands == ["$8", "$9", "42"]
        assert inst.destination == "$8"

    def test_andi(self, parser: MIPSInstructionParser) -> None:
        inst = parser.parse_instruction("andi $t0, $t1, 0xFF", 0)
        assert inst is not None
        assert inst.instruction_type == InstructionType.LOGICAL
        assert inst.operands[2] == "255"

    def test_lw_with_offset(self, parser: MIPSInstructionParser) -> None:
        inst = parser.parse_instruction("lw $t0, 8($sp)", 0)
        assert inst is not None
        assert inst.opcode == "LW"
        assert inst.instruction_type == InstructionType.LOAD
        assert inst.destination == "$8"

    def test_sw_with_offset(self, parser: MIPSInstructionParser) -> None:
        inst = parser.parse_instruction("sw $t0, 4($sp)", 0)
        assert inst is not None
        assert inst.opcode == "SW"
        assert inst.instruction_type == InstructionType.STORE
        assert inst.destination is None

    def test_lw_no_offset(self, parser: MIPSInstructionParser) -> None:
        inst = parser.parse_instruction("lw $t0, ($sp)", 0)
        assert inst is not None
        # Should produce offset=0
        assert "0($29)" in inst.operands[1]

    def test_li(self, parser: MIPSInstructionParser) -> None:
        inst = parser.parse_instruction("li $t0, 100", 0)
        assert inst is not None
        assert inst.opcode == "LI"
        assert inst.destination == "$8"

    def test_ori(self, parser: MIPSInstructionParser) -> None:
        inst = parser.parse_instruction("ori $t0, $t1, 0xFF", 0)
        assert inst is not None
        assert inst.opcode == "ORI"


class TestBranchParsing:
    """Branch instructions with label resolution."""

    def test_beq_with_offset(self, parser: MIPSInstructionParser) -> None:
        inst = parser.parse_instruction("beq $t0, $t1, 5", 0)
        assert inst is not None
        assert inst.opcode == "BEQ"
        assert inst.instruction_type == InstructionType.BRANCH
        # Third operand is the branch offset
        assert inst.operands[2] == "5"

    def test_bne(self, parser: MIPSInstructionParser) -> None:
        inst = parser.parse_instruction("bne $t0, $t1, -3", 0)
        assert inst is not None
        assert inst.opcode == "BNE"

    def test_blez(self, parser: MIPSInstructionParser) -> None:
        inst = parser.parse_instruction("blez $t0, 10", 0)
        assert inst is not None
        assert inst.opcode == "BLEZ"
        assert inst.instruction_type == InstructionType.BRANCH

    def test_bgtz(self, parser: MIPSInstructionParser) -> None:
        inst = parser.parse_instruction("bgtz $t0, 10", 0)
        assert inst is not None
        assert inst.opcode == "BGTZ"

    def test_beq_with_label(self, parser: MIPSInstructionParser) -> None:
        labels = {"loop": 0}
        # beq at address 8, target loop at 0 → offset = (0 - 8 - 4)/4 = -3
        inst = parser.parse_instruction("beq $t0, $t1, loop", 8, labels)
        assert inst is not None
        assert inst.operands[2] == "-3"


# ========================== J-type Instructions =============================


class TestJTypeParsing:
    """Jump instructions."""

    def test_j(self, parser: MIPSInstructionParser) -> None:
        inst = parser.parse_instruction("j 1024", 0)
        assert inst is not None
        assert inst.opcode == "J"
        assert inst.instruction_type == InstructionType.JUMP

    def test_jal(self, parser: MIPSInstructionParser) -> None:
        inst = parser.parse_instruction("jal 2048", 0)
        assert inst is not None
        assert inst.opcode == "JAL"
        assert inst.instruction_type == InstructionType.JUMP

    def test_j_with_label(self, parser: MIPSInstructionParser) -> None:
        labels = {"target": 0x100}
        inst = parser.parse_instruction("j target", 0, labels)
        assert inst is not None
        assert inst.operands[0] == "256"


# ========================== Floating Point ==================================


class TestFloatingPointParsing:
    """IEEE 754 single-precision instructions."""

    def test_add_s(self, parser: MIPSInstructionParser) -> None:
        inst = parser.parse_instruction("add.s $t0, $t1, $t2", 0)
        assert inst is not None
        assert inst.opcode == "ADD.S"
        assert inst.instruction_type == InstructionType.FLOATING_POINT

    def test_mul_s(self, parser: MIPSInstructionParser) -> None:
        inst = parser.parse_instruction("mul.s $t0, $t1, $t2", 0)
        assert inst is not None
        assert inst.opcode == "MUL.S"


# ========================== Program Parsing =================================


class TestParseProgram:
    """Multi-line program parsing with labels and directives."""

    def test_simple_program(self, parser: MIPSInstructionParser) -> None:
        program = """\
        addi $t0, $zero, 10
        addi $t1, $zero, 20
        add $t2, $t0, $t1
        """
        insts = parser.parse_program(program)
        assert len(insts) == 3
        assert insts[0].opcode == "ADDI"
        assert insts[2].opcode == "ADD"

    def test_labels_are_resolved(self, parser: MIPSInstructionParser) -> None:
        program = """\
loop:   addi $t0, $t0, 1
        bne $t0, $t1, loop
        """
        insts = parser.parse_program(program)
        assert len(insts) == 2
        # The second instruction is a branch back to loop (address 0)
        assert insts[1].opcode == "BNE"

    def test_data_section_is_skipped(self, parser: MIPSInstructionParser) -> None:
        program = """\
.data
arr: .word 1 2 3 4
.text
        addi $t0, $zero, 0
        """
        insts = parser.parse_program(program)
        assert len(insts) == 1
        assert insts[0].opcode == "ADDI"

    def test_comments_are_stripped(self, parser: MIPSInstructionParser) -> None:
        program = """\
        addi $t0, $zero, 5  # load 5 into t0
        add $t1, $t0, $t0   # double it
        """
        insts = parser.parse_program(program)
        assert len(insts) == 2

    def test_empty_program(self, parser: MIPSInstructionParser) -> None:
        insts = parser.parse_program("")
        assert insts == []

    def test_instruction_addresses_increment_by_four(
        self, parser: MIPSInstructionParser
    ) -> None:
        program = """\
        add $t0, $t1, $t2
        sub $t3, $t4, $t5
        and $t6, $t7, $t8
        """
        insts = parser.parse_program(program)
        addresses = [inst.address for inst in insts]
        assert addresses == [0, 4, 8]


# ========================== Error Handling ===================================


class TestParserErrors:
    """Invalid input raises ValueError."""

    def test_unknown_opcode(self, parser: MIPSInstructionParser) -> None:
        with pytest.raises(ValueError, match="Unknown instruction"):
            parser.parse_instruction("foobar $t0, $t1", 0)

    def test_too_few_operands_r_type(self, parser: MIPSInstructionParser) -> None:
        with pytest.raises(ValueError):
            parser.parse_instruction("add $t0", 0)

    def test_too_few_operands_shift(self, parser: MIPSInstructionParser) -> None:
        with pytest.raises(ValueError):
            parser.parse_instruction("sll $t0, $t1", 0)
