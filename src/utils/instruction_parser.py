#!/usr/bin/env python3

"""
Enhanced Instruction Parser for MIPS Assembly

This module provides comprehensive MIPS assembly instruction parsing
with support for various instruction formats and operand types.
"""

from enum import Enum
import re
from typing import List, Optional, Union

# Handle imports for both package and direct execution
try:
    from .instruction import Instruction, InstructionType
except (ImportError, ValueError):
    import os
    import sys

    sys.path.insert(0, os.path.dirname(__file__))
    from instruction import Instruction, InstructionType  # type: ignore[no-redef]


class RegisterType(Enum):
    """Register types in MIPS architecture."""

    GENERAL = "general"  # $0-$31
    FLOATING = "floating"  # $f0-$f31
    SPECIAL = "special"  # $hi, $lo, $pc


class InstructionFormat(Enum):
    """MIPS instruction formats."""

    R_TYPE = "R"  # Register format
    I_TYPE = "I"  # Immediate format
    J_TYPE = "J"  # Jump format


class MIPSInstructionParser:
    """
    Comprehensive MIPS assembly instruction parser.

    Supports all major MIPS instruction types with proper operand parsing,
    immediate value handling, and register name resolution.
    """

    def __init__(self) -> None:
        """Initialize the parser with instruction definitions."""
        self._init_instruction_definitions()
        self._init_register_mappings()

    def _init_instruction_definitions(self) -> None:
        """Initialize instruction definitions with formats and types."""
        self.instruction_defs = {
            # Arithmetic R-type instructions
            "add": {
                "format": InstructionFormat.R_TYPE,
                "type": InstructionType.ARITHMETIC,
                "latency": 1,
            },
            "addu": {
                "format": InstructionFormat.R_TYPE,
                "type": InstructionType.ARITHMETIC,
                "latency": 1,
            },
            "sub": {
                "format": InstructionFormat.R_TYPE,
                "type": InstructionType.ARITHMETIC,
                "latency": 1,
            },
            "subu": {
                "format": InstructionFormat.R_TYPE,
                "type": InstructionType.ARITHMETIC,
                "latency": 1,
            },
            "mult": {
                "format": InstructionFormat.R_TYPE,
                "type": InstructionType.ARITHMETIC,
                "latency": 3,
            },
            "multu": {
                "format": InstructionFormat.R_TYPE,
                "type": InstructionType.ARITHMETIC,
                "latency": 3,
            },
            "div": {
                "format": InstructionFormat.R_TYPE,
                "type": InstructionType.ARITHMETIC,
                "latency": 10,
            },
            "divu": {
                "format": InstructionFormat.R_TYPE,
                "type": InstructionType.ARITHMETIC,
                "latency": 10,
            },
            # Arithmetic I-type instructions
            "addi": {
                "format": InstructionFormat.I_TYPE,
                "type": InstructionType.ARITHMETIC,
                "latency": 1,
            },
            "addiu": {
                "format": InstructionFormat.I_TYPE,
                "type": InstructionType.ARITHMETIC,
                "latency": 1,
            },
            # Logical R-type instructions
            "and": {
                "format": InstructionFormat.R_TYPE,
                "type": InstructionType.LOGICAL,
                "latency": 1,
            },
            "or": {
                "format": InstructionFormat.R_TYPE,
                "type": InstructionType.LOGICAL,
                "latency": 1,
            },
            "xor": {
                "format": InstructionFormat.R_TYPE,
                "type": InstructionType.LOGICAL,
                "latency": 1,
            },
            "nor": {
                "format": InstructionFormat.R_TYPE,
                "type": InstructionType.LOGICAL,
                "latency": 1,
            },
            "sll": {
                "format": InstructionFormat.R_TYPE,
                "type": InstructionType.LOGICAL,
                "latency": 1,
            },
            "srl": {
                "format": InstructionFormat.R_TYPE,
                "type": InstructionType.LOGICAL,
                "latency": 1,
            },
            "sra": {
                "format": InstructionFormat.R_TYPE,
                "type": InstructionType.LOGICAL,
                "latency": 1,
            },
            # Logical I-type instructions
            "andi": {
                "format": InstructionFormat.I_TYPE,
                "type": InstructionType.LOGICAL,
                "latency": 1,
            },
            "ori": {
                "format": InstructionFormat.I_TYPE,
                "type": InstructionType.LOGICAL,
                "latency": 1,
            },
            "xori": {
                "format": InstructionFormat.I_TYPE,
                "type": InstructionType.LOGICAL,
                "latency": 1,
            },
            "lui": {
                "format": InstructionFormat.I_TYPE,
                "type": InstructionType.LOGICAL,
                "latency": 1,
            },
            # Comparison instructions
            "slt": {
                "format": InstructionFormat.R_TYPE,
                "type": InstructionType.COMPARISON,
                "latency": 1,
            },
            "sltu": {
                "format": InstructionFormat.R_TYPE,
                "type": InstructionType.COMPARISON,
                "latency": 1,
            },
            "slti": {
                "format": InstructionFormat.I_TYPE,
                "type": InstructionType.COMPARISON,
                "latency": 1,
            },
            "sltiu": {
                "format": InstructionFormat.I_TYPE,
                "type": InstructionType.COMPARISON,
                "latency": 1,
            },
            # Memory instructions
            "lw": {
                "format": InstructionFormat.I_TYPE,
                "type": InstructionType.LOAD,
                "latency": 2,
            },
            "lh": {
                "format": InstructionFormat.I_TYPE,
                "type": InstructionType.LOAD,
                "latency": 2,
            },
            "lhu": {
                "format": InstructionFormat.I_TYPE,
                "type": InstructionType.LOAD,
                "latency": 2,
            },
            "lb": {
                "format": InstructionFormat.I_TYPE,
                "type": InstructionType.LOAD,
                "latency": 2,
            },
            "lbu": {
                "format": InstructionFormat.I_TYPE,
                "type": InstructionType.LOAD,
                "latency": 2,
            },
            "sw": {
                "format": InstructionFormat.I_TYPE,
                "type": InstructionType.STORE,
                "latency": 1,
            },
            "sh": {
                "format": InstructionFormat.I_TYPE,
                "type": InstructionType.STORE,
                "latency": 1,
            },
            "sb": {
                "format": InstructionFormat.I_TYPE,
                "type": InstructionType.STORE,
                "latency": 1,
            },
            # Branch instructions
            "beq": {
                "format": InstructionFormat.I_TYPE,
                "type": InstructionType.BRANCH,
                "latency": 1,
            },
            "bne": {
                "format": InstructionFormat.I_TYPE,
                "type": InstructionType.BRANCH,
                "latency": 1,
            },
            "blez": {
                "format": InstructionFormat.I_TYPE,
                "type": InstructionType.BRANCH,
                "latency": 1,
            },
            "bgtz": {
                "format": InstructionFormat.I_TYPE,
                "type": InstructionType.BRANCH,
                "latency": 1,
            },
            "bltz": {
                "format": InstructionFormat.I_TYPE,
                "type": InstructionType.BRANCH,
                "latency": 1,
            },
            "bgez": {
                "format": InstructionFormat.I_TYPE,
                "type": InstructionType.BRANCH,
                "latency": 1,
            },
            # Jump instructions
            "j": {
                "format": InstructionFormat.J_TYPE,
                "type": InstructionType.JUMP,
                "latency": 1,
            },
            "jal": {
                "format": InstructionFormat.J_TYPE,
                "type": InstructionType.JUMP,
                "latency": 1,
            },
            "jr": {
                "format": InstructionFormat.R_TYPE,
                "type": InstructionType.JUMP,
                "latency": 1,
            },
            "jalr": {
                "format": InstructionFormat.R_TYPE,
                "type": InstructionType.JUMP,
                "latency": 1,
            },
            # Floating point instructions
            "add.s": {
                "format": InstructionFormat.R_TYPE,
                "type": InstructionType.FLOATING_POINT,
                "latency": 4,
            },
            "sub.s": {
                "format": InstructionFormat.R_TYPE,
                "type": InstructionType.FLOATING_POINT,
                "latency": 4,
            },
            "mul.s": {
                "format": InstructionFormat.R_TYPE,
                "type": InstructionType.FLOATING_POINT,
                "latency": 6,
            },
            "div.s": {
                "format": InstructionFormat.R_TYPE,
                "type": InstructionType.FLOATING_POINT,
                "latency": 12,
            },
            # Pseudo-instructions
            "li": {
                "format": InstructionFormat.I_TYPE,
                "type": InstructionType.ARITHMETIC,
                "latency": 1,
            },
            "la": {
                "format": InstructionFormat.I_TYPE,
                "type": InstructionType.ARITHMETIC,
                "latency": 1,
            },
            "move": {
                "format": InstructionFormat.R_TYPE,
                "type": InstructionType.ARITHMETIC,
                "latency": 1,
            },
            "nop": {
                "format": InstructionFormat.R_TYPE,
                "type": InstructionType.NOP,
                "latency": 1,
            },
            # Additional branch instructions
            "bge": {
                "format": InstructionFormat.I_TYPE,
                "type": InstructionType.BRANCH,
                "latency": 1,
            },
            "bgt": {
                "format": InstructionFormat.I_TYPE,
                "type": InstructionType.BRANCH,
                "latency": 1,
            },
            "ble": {
                "format": InstructionFormat.I_TYPE,
                "type": InstructionType.BRANCH,
                "latency": 1,
            },
            "blt": {
                "format": InstructionFormat.I_TYPE,
                "type": InstructionType.BRANCH,
                "latency": 1,
            },
            # System calls
            "syscall": {
                "format": InstructionFormat.R_TYPE,
                "type": InstructionType.SYSTEM,
                "latency": 1,
            },
        }

    def _init_register_mappings(self) -> None:
        """Initialize register name to number mappings."""
        self.register_map = {
            # General purpose registers
            "$zero": 0,
            "$0": 0,
            "$at": 1,
            "$1": 1,
            "$v0": 2,
            "$2": 2,
            "$v1": 3,
            "$3": 3,
            "$a0": 4,
            "$4": 4,
            "$a1": 5,
            "$5": 5,
            "$a2": 6,
            "$6": 6,
            "$a3": 7,
            "$7": 7,
            "$t0": 8,
            "$8": 8,
            "$t1": 9,
            "$9": 9,
            "$t2": 10,
            "$10": 10,
            "$t3": 11,
            "$11": 11,
            "$t4": 12,
            "$12": 12,
            "$t5": 13,
            "$13": 13,
            "$t6": 14,
            "$14": 14,
            "$t7": 15,
            "$15": 15,
            "$s0": 16,
            "$16": 16,
            "$s1": 17,
            "$17": 17,
            "$s2": 18,
            "$18": 18,
            "$s3": 19,
            "$19": 19,
            "$s4": 20,
            "$20": 20,
            "$s5": 21,
            "$21": 21,
            "$s6": 22,
            "$22": 22,
            "$s7": 23,
            "$23": 23,
            "$t8": 24,
            "$24": 24,
            "$t9": 25,
            "$25": 25,
            "$k0": 26,
            "$26": 26,
            "$k1": 27,
            "$27": 27,
            "$gp": 28,
            "$28": 28,
            "$sp": 29,
            "$29": 29,
            "$fp": 30,
            "$30": 30,
            "$ra": 31,
            "$31": 31,
        }

        # Floating point registers
        for i in range(32):
            self.register_map[f"$f{i}"] = i

    def parse_program(self, program_text: str) -> list[Instruction]:
        """
        Parse a complete MIPS assembly program.

        Args:
            program_text: Complete assembly program as string

        Returns:
            List of parsed Instruction objects
        """
        instructions = []
        labels = {}
        data_labels = {}
        current_address = 0
        in_data_section = False
        data_address = 0x10000000  # Start data at standard address

        lines = program_text.strip().split("\n")

        # First pass: collect labels and data labels
        for line_num, line in enumerate(lines, 1):
            line = self._preprocess_line(line)
            if not line:
                continue

            # Check for section directives
            if line.startswith(".data"):
                in_data_section = True
                continue
            elif line.startswith(".text"):
                in_data_section = False
                continue

            if ":" in line and not line.strip().startswith("#"):
                label = line.split(":")[0].strip()

                if in_data_section:
                    # Data label
                    data_labels[label] = data_address
                    # Check if there's a data declaration on the same line
                    remainder = line.split(":", 1)[1].strip()
                    if remainder and remainder.startswith(".word"):
                        # Count words to advance data address
                        words = remainder.split()[1:]  # Skip .word directive
                        data_address += len(words) * 4
                else:
                    # Code label
                    labels[label] = current_address
                    # Check if there's an instruction on the same line
                    remainder = line.split(":", 1)[1].strip()
                    if remainder and not remainder.startswith("."):
                        current_address += 4
            elif (
                not line.startswith(".") and not in_data_section
            ):  # Skip directives and data section
                current_address += 4

        # Merge data labels into labels for instruction parsing
        labels.update(data_labels)

        # Second pass: parse instructions
        current_address = 0
        in_data_section = False

        for line_num, line in enumerate(lines, 1):
            line = self._preprocess_line(line)
            if not line:
                continue

            # Check for section directives
            if line.startswith(".data"):
                in_data_section = True
                continue
            elif line.startswith(".text"):
                in_data_section = False
                continue

            # Skip data section
            if in_data_section:
                continue

            try:
                # Handle labels
                if ":" in line:
                    remainder = line.split(":", 1)[1].strip()
                    if not remainder:
                        continue
                    line = remainder

                # Skip directives
                if line.startswith("."):
                    continue

                instruction = self.parse_instruction(line, current_address, labels)
                if instruction:
                    instructions.append(instruction)
                    current_address += 4

            except Exception as e:
                raise ValueError(
                    f"Parse error at line {line_num}: {line}\nError: {e}"
                ) from e

        return instructions

    def parse_instruction(
        self, line: str, address: int, labels: dict[str, int] | None = None
    ) -> Instruction | None:
        """
        Parse a single MIPS instruction.

        Args:
            line: Assembly instruction line
            address: Instruction address
            labels: Label to address mapping

        Returns:
            Parsed Instruction object or None if invalid
        """
        if labels is None:
            labels = {}

        line = line.strip()
        if not line or line.startswith("#"):
            return None

        # Split instruction and operands
        parts = re.split(r"[,\s]+", line)
        if not parts:
            return None

        opcode = parts[0].lower()
        operands = [op.strip() for op in parts[1:] if op.strip()]

        if opcode not in self.instruction_defs:
            raise ValueError(f"Unknown instruction: {opcode}")

        instr_def = self.instruction_defs[opcode]

        # Parse operands based on instruction format
        if instr_def["format"] == InstructionFormat.R_TYPE:
            return self._parse_r_type(opcode, operands, address, instr_def)
        elif instr_def["format"] == InstructionFormat.I_TYPE:
            return self._parse_i_type(opcode, operands, address, instr_def, labels)
        elif instr_def["format"] == InstructionFormat.J_TYPE:
            return self._parse_j_type(opcode, operands, address, instr_def, labels)

        return None

    def _parse_r_type(
        self, opcode: str, operands: list[str], address: int, instr_def: dict
    ) -> Instruction:
        """Parse R-type instruction."""
        if opcode == "syscall":
            return Instruction(
                opcode=opcode,
                instruction_type=instr_def["type"],
                address=address,
                latency=instr_def["latency"],
            )

        if opcode == "nop":
            return Instruction(
                opcode=opcode,
                instruction_type=instr_def["type"],
                address=address,
                operands=[],
                latency=instr_def["latency"],
            )

        if opcode == "move":
            # Move pseudo-instruction: move rd, rs
            if len(operands) < 2:
                raise ValueError("Move instruction requires 2 operands")
            rd = self._parse_register(operands[0])
            rs = self._parse_register(operands[1])

            return Instruction(
                opcode=opcode,
                instruction_type=instr_def["type"],
                address=address,
                operands=[f"${rd}", f"${rs}"],
                destination=f"${rd}",
                latency=instr_def["latency"],
            )

        if opcode in ["jr", "jalr"]:
            # Jump register instructions
            rs = self._parse_register(operands[0])
            jump_rd = (
                self._parse_register(operands[1])
                if len(operands) > 1 and opcode == "jalr"
                else None
            )

            operands = [f"${rs}"]
            if jump_rd is not None:
                operands.append(f"${jump_rd}")

            return Instruction(
                opcode=opcode,
                instruction_type=instr_def["type"],
                address=address,
                operands=operands,  # type: ignore[arg-type]
                latency=instr_def["latency"],
            )

        # Shift instructions: op rd, rt, shamt
        if opcode in ["sll", "srl", "sra"]:
            if len(operands) < 3:
                raise ValueError(f"Shift instruction {opcode} requires 3 operands")
            rd = self._parse_register(operands[0])
            rt = self._parse_register(operands[1])
            shamt = self._parse_immediate(operands[2])  # Shift amount is immediate

            return Instruction(
                opcode=opcode,
                instruction_type=instr_def["type"],
                address=address,
                operands=[f"${rd}", f"${rt}", str(shamt)],
                destination=f"${rd}",
                latency=instr_def["latency"],
            )

        # Standard R-type: op rd, rs, rt
        if len(operands) < 3:
            raise ValueError(f"R-type instruction {opcode} requires 3 operands")

        rd = self._parse_register(operands[0])
        rs = self._parse_register(operands[1])
        rt = self._parse_register(operands[2])

        return Instruction(
            opcode=opcode,
            instruction_type=instr_def["type"],
            address=address,
            operands=[f"${rd}", f"${rs}", f"${rt}"],
            destination=f"${rd}",
            latency=instr_def["latency"],
        )

    def _parse_i_type(
        self,
        opcode: str,
        operands: list[str],
        address: int,
        instr_def: dict,
        labels: dict[str, int],
    ) -> Instruction:
        """Parse I-type instruction."""
        if opcode in ["lw", "lh", "lhu", "lb", "lbu", "sw", "sh", "sb"]:
            # Memory instructions: op rt, offset(rs)
            rt = self._parse_register(operands[0])
            offset_rs = operands[1]

            # Parse offset(rs) format
            if "(" in offset_rs:
                offset_str, rs_str = offset_rs.split("(")
                rs = self._parse_register(rs_str.rstrip(")"))
                immediate = self._parse_immediate(offset_str) if offset_str else 0
            else:
                rs = self._parse_register(offset_rs)
                immediate = 0

            return Instruction(
                opcode=opcode,
                instruction_type=instr_def["type"],
                address=address,
                operands=[f"${rt}", f"{immediate}(${rs})"],
                destination=f"${rt}" if opcode.startswith("l") else None,
                latency=instr_def["latency"],
            )

        elif opcode in ["beq", "bne", "bge", "bgt", "ble", "blt"]:
            # Branch instructions: op rs, rt, label
            rs = self._parse_register(operands[0])
            rt = self._parse_register(operands[1])
            target = self._parse_branch_target(operands[2], address, labels)

            return Instruction(
                opcode=opcode,
                instruction_type=instr_def["type"],
                address=address,
                operands=[f"${rs}", f"${rt}", str(target)],
                latency=instr_def["latency"],
            )

        elif opcode in ["blez", "bgtz", "bltz", "bgez"]:
            # Single register branch: op rs, label
            rs = self._parse_register(operands[0])
            target = self._parse_branch_target(operands[1], address, labels)

            return Instruction(
                opcode=opcode,
                instruction_type=instr_def["type"],
                address=address,
                operands=[f"${rs}", str(target)],
                latency=instr_def["latency"],
            )

        elif opcode in ["li", "la"]:
            # Load immediate/address: li/la rt, immediate/label
            rt = self._parse_register(operands[0])
            if opcode == "la" and operands[1] in labels:
                # Load address of label
                immediate = labels[operands[1]]
            else:
                immediate = self._parse_immediate(operands[1])

            return Instruction(
                opcode=opcode,
                instruction_type=instr_def["type"],
                address=address,
                operands=[f"${rt}", str(immediate)],
                destination=f"${rt}",
                latency=instr_def["latency"],
            )

        else:
            # Standard I-type: op rt, rs, immediate
            rt = self._parse_register(operands[0])
            rs = self._parse_register(operands[1])
            immediate = self._parse_immediate(operands[2])

            return Instruction(
                opcode=opcode,
                instruction_type=instr_def["type"],
                address=address,
                operands=[f"${rt}", f"${rs}", str(immediate)],
                destination=f"${rt}",
                latency=instr_def["latency"],
            )

    def _parse_j_type(
        self,
        opcode: str,
        operands: list[str],
        address: int,
        instr_def: dict,
        labels: dict[str, int],
    ) -> Instruction:
        """Parse J-type instruction."""
        target = self._parse_jump_target(operands[0], labels)

        return Instruction(
            opcode=opcode,
            instruction_type=instr_def["type"],
            address=address,
            operands=[str(target)],
            latency=instr_def["latency"],
        )

    def _parse_register(self, reg_str: str) -> int:
        """Parse register name to register number."""
        reg_str = reg_str.strip()
        if reg_str in self.register_map:
            return self.register_map[reg_str]

        # Try parsing as direct number
        if reg_str.startswith("$") and reg_str[1:].isdigit():
            reg_num = int(reg_str[1:])
            if 0 <= reg_num <= 31:
                return reg_num

        raise ValueError(f"Invalid register: {reg_str}")

    def _parse_immediate(self, imm_str: str) -> int:
        """Parse immediate value."""
        imm_str = imm_str.strip()

        # Handle different number formats
        if imm_str.startswith("0x"):
            return int(imm_str, 16)
        elif imm_str.startswith("0b"):
            return int(imm_str, 2)
        else:
            return int(imm_str)

    def _parse_branch_target(
        self, target_str: str, current_addr: int, labels: dict[str, int]
    ) -> int:
        """Parse branch target (label or offset)."""
        target_str = target_str.strip()

        if target_str in labels:
            # Calculate relative offset
            target_addr = labels[target_str]
            return (target_addr - current_addr - 4) // 4
        else:
            # Direct offset
            return self._parse_immediate(target_str)

    def _parse_jump_target(self, target_str: str, labels: dict[str, int]) -> int:
        """Parse jump target (label or address)."""
        target_str = target_str.strip()

        if target_str in labels:
            return labels[target_str]
        else:
            return self._parse_immediate(target_str)

    def _preprocess_line(self, line: str) -> str:
        """Preprocess assembly line (remove comments, normalize whitespace)."""
        # Remove comments
        if "#" in line:
            line = line[: line.index("#")]

        # Normalize whitespace
        line = re.sub(r"\s+", " ", line.strip())

        return line
