"""
Instruction Class Implementation

This module defines the Instruction class and related utilities for representing
and manipulating processor instructions in the superscalar pipeline simulator.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional, Union


class InstructionType(Enum):
    """Enumeration of instruction types."""
    ARITHMETIC = "arithmetic"
    LOGICAL = "logical"
    MEMORY = "memory"
    BRANCH = "branch"
    JUMP = "jump"
    FLOAT = "float"
    NOP = "nop"


class InstructionStatus(Enum):
    """Enumeration of instruction pipeline states."""
    FETCHED = "fetched"
    DECODED = "decoded"
    ISSUED = "issued"
    EXECUTING = "executing"
    MEMORY_ACCESS = "memory_access"
    WRITE_BACK = "write_back"
    COMPLETED = "completed"


@dataclass
class Instruction:
    """
    Represents a processor instruction with all necessary metadata.
    
    Attributes:
        address: Memory address of the instruction
        opcode: Operation code (e.g., "ADD", "LW", "BEQ")
        operands: List of operand values/registers
        destination: Destination register (if applicable)
        instruction_type: Type of instruction
        status: Current pipeline status
        issue_cycle: Cycle when instruction was issued
        completion_cycle: Cycle when instruction completed
        result: Result of instruction execution
        prediction_info: Branch prediction metadata
    """

    address: int
    opcode: str
    operands: List[Union[str, int]] = field(default_factory=list)
    destination: Optional[str] = None
    instruction_type: Optional[InstructionType] = None
    status: InstructionStatus = InstructionStatus.FETCHED
    issue_cycle: Optional[int] = None
    completion_cycle: Optional[int] = None
    result: Optional[Any] = None
    prediction_info: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Initialize instruction type based on opcode if not provided."""
        if self.instruction_type is None:
            self.instruction_type = self._determine_type()

        # Normalize opcode to uppercase
        self.opcode = self.opcode.upper()

        # Parse destination from operands if not explicitly set
        if self.destination is None and self.has_destination_register():
            self._parse_destination()

    def _determine_type(self) -> InstructionType:
        """Determine instruction type from opcode."""
        opcode_upper = self.opcode.upper()

        if opcode_upper in ["ADD", "SUB", "MUL", "DIV", "ADDI", "SUBI"]:
            return InstructionType.ARITHMETIC
        elif opcode_upper in ["AND", "OR", "XOR", "SLT", "ANDI", "ORI", "XORI", "SLTI"]:
            return InstructionType.LOGICAL
        elif opcode_upper in ["LW", "SW", "LB", "LH", "SB", "SH"]:
            return InstructionType.MEMORY
        elif opcode_upper in ["BEQ", "BNE", "BLT", "BGE", "BLTU", "BGEU"]:
            return InstructionType.BRANCH
        elif opcode_upper in ["J", "JAL", "JR", "JALR"]:
            return InstructionType.JUMP
        elif opcode_upper in ["FADD", "FSUB", "FMUL", "FDIV"]:
            return InstructionType.FLOAT
        elif opcode_upper == "NOP":
            return InstructionType.NOP
        else:
            # Default to arithmetic for unknown opcodes
            return InstructionType.ARITHMETIC

    def _parse_destination(self) -> None:
        """Parse destination register from operands based on instruction format."""
        if self.is_r_type() and len(self.operands) >= 3:
            # R-type: op rd, rs1, rs2
            self.destination = self.operands[0]
        elif self.is_i_type() and len(self.operands) >= 2:
            # I-type: op rd, rs1, imm
            self.destination = self.operands[0]
        elif self.opcode.upper() in ["JAL", "JALR"] and len(self.operands) >= 1:
            # Jump and link saves return address
            self.destination = "$ra"  # Return address register

    def is_r_type(self) -> bool:
        """Check if this is an R-type instruction (register-register)."""
        return self.opcode.upper() in ["ADD", "SUB", "MUL", "DIV", "AND", "OR", "XOR", "SLT",
                                       "FADD", "FSUB", "FMUL", "FDIV"]

    def is_i_type(self) -> bool:
        """Check if this is an I-type instruction (register-immediate)."""
        return self.opcode.upper() in ["ADDI", "SUBI", "ANDI", "ORI", "XORI", "SLTI",
                                       "LW", "LB", "LH"]

    def is_s_type(self) -> bool:
        """Check if this is an S-type instruction (store)."""
        return self.opcode.upper() in ["SW", "SB", "SH"]

    def is_memory_operation(self) -> bool:
        """Check if this instruction performs memory access."""
        return self.instruction_type == InstructionType.MEMORY

    def is_load(self) -> bool:
        """Check if this is a load instruction."""
        return self.opcode.upper() in ["LW", "LB", "LH"]

    def is_store(self) -> bool:
        """Check if this is a store instruction."""
        return self.opcode.upper() in ["SW", "SB", "SH"]

    def is_branch(self) -> bool:
        """Check if this is a branch instruction."""
        return self.instruction_type in [InstructionType.BRANCH, InstructionType.JUMP]

    def is_conditional_branch(self) -> bool:
        """Check if this is a conditional branch."""
        return self.instruction_type == InstructionType.BRANCH

    def is_jump(self) -> bool:
        """Check if this is a jump instruction."""
        return self.instruction_type == InstructionType.JUMP

    def is_arithmetic(self) -> bool:
        """Check if this is an arithmetic instruction."""
        return self.instruction_type == InstructionType.ARITHMETIC

    def is_logical(self) -> bool:
        """Check if this is a logical instruction."""
        return self.instruction_type == InstructionType.LOGICAL

    def is_floating_point(self) -> bool:
        """Check if this is a floating-point instruction."""
        return self.instruction_type == InstructionType.FLOAT

    def has_destination_register(self) -> bool:
        """Check if this instruction writes to a destination register."""
        # Store and branch instructions don't have destinations
        return not (self.is_store() or self.is_branch())

    def get_destination_register(self) -> Optional[str]:
        """Get the destination register name."""
        return self.destination

    def get_source_registers(self) -> List[str]:
        """Get list of source register names."""
        sources = []

        if self.is_r_type():
            # R-type: rd, rs1, rs2
            if len(self.operands) >= 3:
                sources.extend([self.operands[1], self.operands[2]])
        elif self.is_i_type():
            # I-type: rd, rs1, imm
            if len(self.operands) >= 2:
                sources.append(self.operands[1])
        elif self.is_s_type():
            # S-type: rs2, offset(rs1)
            if len(self.operands) >= 2:
                # Parse both source registers
                sources.append(self.operands[0])  # Value to store
                # Parse base register from offset(base) format
                if isinstance(self.operands[1], str) and '(' in self.operands[1]:
                    base_reg = self.operands[1].split('(')[1].rstrip(')')
                    sources.append(base_reg)
        elif self.is_conditional_branch():
            # Branch: rs1, rs2, target
            if len(self.operands) >= 2:
                sources.extend([self.operands[0], self.operands[1]])

        return sources

    def get_memory_address(self) -> Optional[int]:
        """Get memory address for load/store instructions."""
        if not self.is_memory_operation():
            return None

        # For load/store, parse the offset(base) format
        if len(self.operands) >= 1:
            addr_operand = self.operands[1] if self.is_load() else self.operands[0]
            if isinstance(addr_operand, int):
                return addr_operand

        return None

    def is_taken(self, register_file) -> bool:
        """
        Determine if a branch instruction is taken.
        
        Args:
            register_file: Register file to read register values
            
        Returns:
            True if branch is taken, False otherwise
        """
        opcode = self.opcode.upper()

        if opcode == "BEQ":
            rs1 = register_file.read_register(self.operands[0])
            rs2 = register_file.read_register(self.operands[1])
            return rs1 == rs2
        elif opcode == "BNE":
            rs1 = register_file.read_register(self.operands[0])
            rs2 = register_file.read_register(self.operands[1])
            return rs1 != rs2
        elif opcode == "BLT":
            rs1 = register_file.read_register(self.operands[0])
            rs2 = register_file.read_register(self.operands[1])
            return rs1 < rs2
        elif opcode == "BGE":
            rs1 = register_file.read_register(self.operands[0])
            rs2 = register_file.read_register(self.operands[1])
            return rs1 >= rs2
        elif opcode in ["J", "JAL"]:
            # Unconditional jumps are always taken
            return True
        elif opcode in ["JR", "JALR"]:
            # Register jumps are always taken
            return True
        else:
            return False

    def get_latency(self) -> int:
        """Get expected execution latency for this instruction."""
        latency_map = {
            "ADD": 1, "SUB": 1, "ADDI": 1, "SUBI": 1,
            "AND": 1, "OR": 1, "XOR": 1, "SLT": 1,
            "ANDI": 1, "ORI": 1, "XORI": 1, "SLTI": 1,
            "MUL": 3, "DIV": 10,
            "FADD": 3, "FSUB": 3, "FMUL": 5, "FDIV": 15,
            "LW": 2, "SW": 2, "LB": 2, "LH": 2, "SB": 2, "SH": 2,
            "BEQ": 1, "BNE": 1, "BLT": 1, "BGE": 1,
            "J": 1, "JAL": 1, "JR": 1, "JALR": 1,
            "NOP": 1
        }
        return latency_map.get(self.opcode.upper(), 1)

    def __repr__(self) -> str:
        """String representation of the instruction."""
        operands_str = ", ".join(str(op) for op in self.operands)
        return f"Instruction(PC={self.address:#x}, {self.opcode} {operands_str})"

    def __str__(self) -> str:
        """Human-readable string representation."""
        operands_str = ", ".join(str(op) for op in self.operands)
        return f"{self.opcode} {operands_str}"


@dataclass
class BranchInstruction(Instruction):
    """
    Specialized instruction class for branch instructions.
    
    Adds branch-specific attributes and methods.
    """

    pc: int = 0  # Alias for address
    condition: Optional[bool] = None  # For conditional branches
    target_address: Optional[int] = None

    def __post_init__(self) -> None:
        """Initialize branch instruction."""
        # Set address from pc if not already set
        if self.address == 0 and self.pc != 0:
            self.address = self.pc
        elif self.pc == 0 and self.address != 0:
            self.pc = self.address

        # Ensure it's marked as a branch
        if not self.opcode:
            self.opcode = "BEQ"  # Default branch opcode

        super().__post_init__()

        # Calculate target address if not set
        if self.target_address is None and len(self.operands) >= 1:
            try:
                if self.opcode.upper() in ['J', 'JAL']:
                    # Jump instructions: operand is absolute address
                    target_str = self.operands[0]
                    if target_str.startswith('0x'):
                        self.target_address = int(target_str, 16)
                    else:
                        self.target_address = int(target_str)
                elif len(self.operands) >= 3:
                    # Branch instructions: operand is offset
                    offset = int(self.operands[2])
                    self.target_address = self.address + 4 + (offset * 4)
            except (ValueError, IndexError):
                pass

    def get_target_address(self) -> Optional[int]:
        """Get the target address for this branch."""
        return self.target_address


class InstructionBundle:
    """
    Represents a bundle of instructions fetched together in superscalar execution.
    """

    def __init__(self, instructions: List[Instruction], fetch_cycle: int) -> None:
        """
        Initialize instruction bundle.
        
        Args:
            instructions: List of instructions in the bundle
            fetch_cycle: Cycle when bundle was fetched
        """
        self.instructions = instructions
        self.fetch_cycle = fetch_cycle
        self.size = len(instructions)

    def has_branch(self) -> bool:
        """Check if bundle contains a branch instruction."""
        return any(inst.is_branch() for inst in self.instructions)

    def get_branch_instruction(self) -> Optional[Instruction]:
        """Get the first branch instruction in the bundle."""
        for inst in self.instructions:
            if inst.is_branch():
                return inst
        return None

    def has_memory_operation(self) -> bool:
        """Check if bundle contains memory operations."""
        return any(inst.is_memory_operation() for inst in self.instructions)

    def get_dependencies(self) -> List[tuple[int, int]]:
        """
        Get RAW dependencies within the bundle.
        
        Returns:
            List of (producer_idx, consumer_idx) tuples
        """
        dependencies = []

        for i in range(self.size):
            if self.instructions[i].has_destination_register():
                dest = self.instructions[i].get_destination_register()

                # Check if any later instruction uses this destination
                for j in range(i + 1, self.size):
                    sources = self.instructions[j].get_source_registers()
                    if dest in sources:
                        dependencies.append((i, j))

        return dependencies

    def __repr__(self) -> str:
        """String representation of the bundle."""
        return f"InstructionBundle(size={self.size}, cycle={self.fetch_cycle})"
