"""
Functional Unit Implementation

This module provides the base class and specialized implementations for functional units
in the superscalar pipeline, including ALU, FPU, and LSU.

Author: Mudit Bhargava
Date: August2025
Python Version: 3.10+
"""

from __future__ import annotations

from typing import Any, Optional

# Handle imports for both package and direct execution
try:
    from ..cache.cache import DataCache, Memory
    from ..register_file.register_file import RegisterFile
except (ImportError, ValueError):
    # Fallback for direct execution
    import os
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    from cache.cache import DataCache, Memory
    from register_file.register_file import RegisterFile
from .instruction import Instruction


class FunctionalUnit:
    """
    Base class for functional units in the processor pipeline.
    
    Attributes:
        id: Unique identifier for the functional unit
        supported_opcodes: List of opcodes this unit can execute
        busy: Whether the unit is currently executing an instruction
        remaining_cycles: Cycles left until current operation completes
        current_instruction: The instruction currently being executed
    """

    def __init__(self, id: int, supported_opcodes: List[str]) -> None:
        """
        Initialize a functional unit.
        
        Args:
            id: Unique identifier for this unit
            supported_opcodes: List of instruction opcodes this unit can execute
        """
        self.id = id
        self.supported_opcodes = supported_opcodes
        self.busy = False
        self.remaining_cycles = 0
        self.current_instruction: Optional[Instruction] = None
        self.result: Optional[Any] = None

    def is_free(self) -> bool:
        """Check if the functional unit is available for use."""
        return not self.busy

    def can_execute(self, opcode: str) -> bool:
        """
        Check if this unit can execute the given opcode.
        
        Args:
            opcode: The instruction opcode to check
            
        Returns:
            True if the unit supports this opcode, False otherwise
        """
        return opcode.upper() in [op.upper() for op in self.supported_opcodes]

    def execute(self, instruction: Instruction, register_file: RegisterFile) -> Optional[Any]:
        """
        Execute an instruction on this functional unit.
        
        Args:
            instruction: The instruction to execute
            register_file: The register file for reading operands
            
        Returns:
            The result of the execution (may be None for some operations)
            
        Raises:
            ValueError: If the opcode is not supported or operation fails
        """
        if not self.can_execute(instruction.opcode):
            raise ValueError(
                f"Unsupported opcode '{instruction.opcode}' for functional unit {self.id}"
            )

        self.busy = True
        self.current_instruction = instruction
        self.remaining_cycles = self.get_execution_latency(instruction.opcode)

        # Actual execution is handled by subclasses
        return self._perform_operation(instruction, register_file)

    def _perform_operation(self, instruction: Instruction, register_file: RegisterFile) -> Optional[Any]:
        """
        Perform the actual operation. To be overridden by subclasses.
        
        Args:
            instruction: The instruction to execute
            register_file: The register file for reading operands
            
        Returns:
            The result of the operation
        """
        raise NotImplementedError("Subclasses must implement _perform_operation")

    def update(self) -> Optional[tuple[Instruction, Any]]:
        """
        Update the functional unit state for one clock cycle.
        
        Returns:
            A tuple of (instruction, result) if operation completed, None otherwise
        """
        if self.busy:
            self.remaining_cycles -= 1
            if self.remaining_cycles <= 0:
                self.busy = False
                completed_instruction = self.current_instruction
                result = self.result
                self.current_instruction = None
                self.result = None
                return (completed_instruction, result)
        return None

    def get_execution_latency(self, opcode: str) -> int:
        """
        Get the execution latency for a given opcode.
        
        Args:
            opcode: The instruction opcode
            
        Returns:
            Number of cycles required to execute this opcode
        """
        # Default latencies - can be overridden by subclasses
        latencies = {
            "ADD": 1,
            "SUB": 1,
            "MUL": 3,
            "DIV": 10,
            "AND": 1,
            "OR": 1,
            "XOR": 1,
            "SLT": 1,
            "LW": 2,
            "SW": 2,
            "FADD": 3,
            "FSUB": 3,
            "FMUL": 5,
            "FDIV": 15,
        }
        return latencies.get(opcode.upper(), 1)

    def __repr__(self) -> str:
        """String representation of the functional unit."""
        return f"{self.__class__.__name__}(id={self.id}, busy={self.busy})"


class ALU(FunctionalUnit):
    """
    Arithmetic Logic Unit for integer operations.
    
    Supports: ADD, SUB, MUL, DIV, AND, OR, XOR, SLT
    """

    def __init__(self, id: int) -> None:
        super().__init__(
            id,
            supported_opcodes=["ADD", "SUB", "MUL", "DIV", "AND", "OR", "XOR", "SLT",
                             "ADDI", "SUBI", "ANDI", "ORI", "XORI", "SLTI"]
        )

    def _perform_operation(self, instruction: Instruction, register_file: RegisterFile) -> int:
        """
        Perform ALU operations.
        
        Args:
            instruction: The instruction to execute
            register_file: The register file for reading operands
            
        Returns:
            The result of the ALU operation
        """
        opcode = instruction.opcode.upper()

        # Get operands - MIPS format: destination, source1, source2/immediate
        if len(instruction.operands) >= 3:
            rs1_val = register_file.read_register(instruction.operands[1])  # source1
            
            if opcode.endswith('I'):
                # Immediate operations: ADDI $rt, $rs, immediate
                try:
                    rs2_val = int(instruction.operands[2])  # immediate value
                except ValueError as e:
                    raise ValueError(f"Invalid immediate value: {instruction.operands[2]}") from e
            else:
                # Register-register operations: ADD $rd, $rs, $rt
                rs2_val = register_file.read_register(instruction.operands[2])  # source2
        else:
            raise ValueError(f"Insufficient operands for {opcode}")

        # Perform operation
        if opcode in ["ADD", "ADDI"]:
            result = rs1_val + rs2_val
        elif opcode in ["SUB", "SUBI"]:
            result = rs1_val - rs2_val
        elif opcode == "MUL":
            result = rs1_val * rs2_val
        elif opcode == "DIV":
            if rs2_val == 0:
                raise ValueError("Division by zero")
            result = rs1_val // rs2_val
        elif opcode in ["AND", "ANDI"]:
            result = rs1_val & rs2_val
        elif opcode in ["OR", "ORI"]:
            result = rs1_val | rs2_val
        elif opcode in ["XOR", "XORI"]:
            result = rs1_val ^ rs2_val
        elif opcode in ["SLT", "SLTI"]:
            result = 1 if rs1_val < rs2_val else 0
        else:
            raise ValueError(f"Unsupported ALU operation: {opcode}")

        self.result = result
        return result


class FPU(FunctionalUnit):
    """
    Floating Point Unit for floating-point operations.
    
    Supports: FADD, FSUB, FMUL, FDIV
    """

    def __init__(self, id: int) -> None:
        super().__init__(
            id,
            supported_opcodes=["FADD", "FSUB", "FMUL", "FDIV"]
        )

    def _perform_operation(self, instruction: Instruction, register_file: RegisterFile) -> float:
        """
        Perform floating-point operations.
        
        Args:
            instruction: The instruction to execute
            register_file: The register file for reading operands
            
        Returns:
            The result of the FPU operation
        """
        opcode = instruction.opcode.upper()

        # Get operands
        if len(instruction.operands) >= 2:
            rs1_val = float(register_file.read_register(instruction.operands[0]))
            rs2_val = float(register_file.read_register(instruction.operands[1]))
        else:
            raise ValueError(f"Insufficient operands for {opcode}")

        # Perform operation
        if opcode == "FADD":
            result = rs1_val + rs2_val
        elif opcode == "FSUB":
            result = rs1_val - rs2_val
        elif opcode == "FMUL":
            result = rs1_val * rs2_val
        elif opcode == "FDIV":
            if rs2_val == 0.0:
                raise ValueError("Floating-point division by zero")
            result = rs1_val / rs2_val
        else:
            raise ValueError(f"Unsupported FPU operation: {opcode}")

        self.result = result
        return result


class LSU(FunctionalUnit):
    """
    Load-Store Unit for memory operations.
    
    Supports: LW (load word), SW (store word)
    """

    def __init__(self, id: int, data_cache: DataCache, memory: Memory) -> None:
        """
        Initialize the LSU.
        
        Args:
            id: Unique identifier for this unit
            data_cache: Reference to the data cache
            memory: Reference to main memory
        """
        super().__init__(
            id,
            supported_opcodes=["LW", "SW", "LB", "LH", "SB", "SH"]
        )
        self.data_cache = data_cache
        self.memory = memory

    def _perform_operation(self, instruction: Instruction, register_file: RegisterFile) -> Optional[int]:
        """
        Perform memory operations.
        
        Args:
            instruction: The instruction to execute
            register_file: The register file for reading operands
            
        Returns:
            The loaded value for load operations, None for store operations
        """
        opcode = instruction.opcode.upper()

        # Parse memory operand format: offset(base)
        # Example: 8($t0) means offset=8, base=register $t0
        if len(instruction.operands) >= 1:
            # For load/store, operand format might be "offset(base)" or separate
            mem_operand = instruction.operands[0]
            if isinstance(mem_operand, str) and '(' in mem_operand:
                # Parse offset(base) format
                offset_str, base_str = mem_operand.split('(')
                offset = int(offset_str) if offset_str else 0
                base_reg = base_str.rstrip(')')
                base_addr = register_file.read_register(base_reg)
            else:
                # Assume separate offset and base
                base_addr = register_file.read_register(instruction.operands[0])
                offset = int(instruction.operands[1]) if len(instruction.operands) > 1 else 0

            address = base_addr + offset
        else:
            raise ValueError(f"Invalid memory operand format for {opcode}")

        # Perform memory operation
        if opcode == "LW":
            # Load word (32-bit)
            if self.data_cache.has_data(address):
                result = self.data_cache.get_data(address)
            else:
                result = self.memory.read(address)
                self.data_cache.add_data(address, result)
            self.result = result
            return result
        elif opcode == "SW":
            # Store word (32-bit)
            if len(instruction.operands) >= 2:
                # Get value to store from register
                store_reg = instruction.operands[-1]  # Last operand is the source register
                data = register_file.read_register(store_reg)

                # Write to cache and memory
                self.data_cache.add_data(address, data)
                self.memory.write(address, data)
                self.result = None
                return None
            else:
                raise ValueError("Store instruction missing source register")
        else:
            raise ValueError(f"Unsupported LSU operation: {opcode}")


# Performance counters for functional units
class FunctionalUnitStats:
    """
    Track performance statistics for functional units.
    """

    def __init__(self) -> None:
        self.unit_usage: Dict[int, int] = {}  # unit_id -> usage count
        self.opcode_counts: Dict[str, int] = {}  # opcode -> execution count
        self.total_stalls = 0
        self.total_cycles = 0

    def record_execution(self, unit_id: int, opcode: str) -> None:
        """Record that a unit executed an instruction."""
        self.unit_usage[unit_id] = self.unit_usage.get(unit_id, 0) + 1
        self.opcode_counts[opcode] = self.opcode_counts.get(opcode, 0) + 1

    def record_stall(self) -> None:
        """Record a structural stall due to all units being busy."""
        self.total_stalls += 1

    def update_cycle(self) -> None:
        """Update cycle counter."""
        self.total_cycles += 1

    def get_utilization(self, unit_id: int) -> float:
        """Get utilization percentage for a specific unit."""
        if self.total_cycles == 0:
            return 0.0
        return (self.unit_usage.get(unit_id, 0) / self.total_cycles) * 100

    def get_opcode_distribution(self) -> Dict[str, float]:
        """Get percentage distribution of executed opcodes."""
        total_ops = sum(self.opcode_counts.values())
        if total_ops == 0:
            return {}

        return {
            opcode: (count / total_ops) * 100
            for opcode, count in self.opcode_counts.items()
        }

    def get_structural_stall_rate(self) -> float:
        """Get the percentage of cycles with structural stalls."""
        if self.total_cycles == 0:
            return 0.0
        return (self.total_stalls / self.total_cycles) * 100
