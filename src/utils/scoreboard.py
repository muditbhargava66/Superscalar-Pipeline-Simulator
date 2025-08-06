"""
Scoreboard Implementation

This module implements the scoreboard for tracking register and functional
unit status to detect and prevent hazards in the pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import logging
from typing import Any, Optional, Union

from .instruction import Instruction

# Handle imports for both package and direct execution
try:
    from ..register_file.register_file import RegisterFile
except (ImportError, ValueError):
    # Fallback for direct execution
    import os
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    from register_file.register_file import RegisterFile


class HazardType(Enum):
    """Types of pipeline hazards."""
    RAW = "Read After Write"  # True dependency
    WAR = "Write After Read"  # Anti-dependency
    WAW = "Write After Write" # Output dependency
    STRUCTURAL = "Structural"  # Resource conflict


@dataclass
class RegisterStatus:
    """Status of a register in the scoreboard."""
    busy: bool = False
    writing_instruction: Optional[Instruction] = None
    reading_instructions: List[Instruction] = field(default_factory=list)
    last_write_cycle: int = -1


@dataclass
class FunctionalUnitStatus:
    """Status of a functional unit."""
    busy: bool = False
    instruction: Optional[Instruction] = None
    remaining_cycles: int = 0
    result_ready: bool = False


class Scoreboard:
    """
    Scoreboard for hazard detection and resource tracking.
    
    Tracks:
    - Register read/write status
    - Functional unit availability
    - Instruction dependencies
    - Hazard detection
    """

    def __init__(self, num_registers: int = 32) -> None:
        """
        Initialize the scoreboard.
        
        Args:
            num_registers: Number of registers to track
        """
        self.num_registers = num_registers

        # Register status tracking
        self.register_status: List[RegisterStatus] = [
            RegisterStatus() for _ in range(num_registers)
        ]

        # Functional unit status
        self.function_unit_status: Dict[str, FunctionalUnitStatus] = {}

        # Instruction tracking
        self.active_instructions: Dict[int, Instruction] = {}  # id -> instruction
        self.instruction_dependencies: Dict[int, Set[int]] = {}  # id -> dependent ids

        # Statistics
        self.hazard_counts = {
            HazardType.RAW: 0,
            HazardType.WAR: 0,
            HazardType.WAW: 0,
            HazardType.STRUCTURAL: 0
        }

        self.current_cycle = 0

        logging.debug(f"Initialized Scoreboard for {num_registers} registers")

    def _resolve_register(self, register: Union[str, int]) -> int:
        """Resolve register identifier to number."""
        if isinstance(register, int):
            return register

        # Handle MIPS register names
        if isinstance(register, str) and hasattr(RegisterFile, 'REGISTER_NAMES') and register in RegisterFile.REGISTER_NAMES:
            return RegisterFile.REGISTER_NAMES[register]

        # Try to parse as number
        if isinstance(register, str):
            if register.startswith('$') and register[1:].isdigit() or register.startswith('r') and register[1:].isdigit():
                return int(register[1:])

        raise ValueError(f"Invalid register: {register}")

    def check_hazards(self, instruction: Instruction) -> List[HazardType]:
        """
        Check for all hazards for an instruction.
        
        Args:
            instruction: Instruction to check
            
        Returns:
            List of detected hazards
        """
        hazards = []

        # Check RAW hazards
        if self.check_raw_hazard(instruction):
            hazards.append(HazardType.RAW)

        # Check WAR hazards
        if self.check_war_hazard(instruction):
            hazards.append(HazardType.WAR)

        # Check WAW hazards
        if self.check_waw_hazard(instruction):
            hazards.append(HazardType.WAW)

        # Check structural hazards
        if self.check_structural_hazard(instruction):
            hazards.append(HazardType.STRUCTURAL)

        return hazards

    def check_raw_hazard(self, instruction: Instruction) -> bool:
        """
        Check for Read-After-Write hazards.
        
        Args:
            instruction: Instruction to check
            
        Returns:
            True if RAW hazard exists
        """
        source_registers = instruction.get_source_registers()

        for src_reg in source_registers:
            try:
                reg_num = self._resolve_register(src_reg)

                # Check if register is being written by another instruction
                if self.register_status[reg_num].busy:
                    writer = self.register_status[reg_num].writing_instruction
                    if writer and writer != instruction:
                        logging.debug(f"RAW hazard: {instruction} depends on {writer}")
                        self.hazard_counts[HazardType.RAW] += 1
                        return True

            except ValueError:
                continue  # Skip invalid registers

        return False

    def check_war_hazard(self, instruction: Instruction) -> bool:
        """
        Check for Write-After-Read hazards.
        
        Args:
            instruction: Instruction to check
            
        Returns:
            True if WAR hazard exists
        """
        if not instruction.has_destination_register():
            return False

        dest_reg = instruction.get_destination_register()
        if not dest_reg:
            return False

        try:
            reg_num = self._resolve_register(dest_reg)

            # Check if register is being read by other instructions
            readers = self.register_status[reg_num].reading_instructions
            if readers:
                for reader in readers:
                    if reader != instruction:
                        logging.debug(f"WAR hazard: {instruction} writes after {reader} reads")
                        self.hazard_counts[HazardType.WAR] += 1
                        return True

        except ValueError:
            pass

        return False

    def check_waw_hazard(self, instruction: Instruction) -> bool:
        """
        Check for Write-After-Write hazards.
        
        Args:
            instruction: Instruction to check
            
        Returns:
            True if WAW hazard exists
        """
        if not instruction.has_destination_register():
            return False

        dest_reg = instruction.get_destination_register()
        if not dest_reg:
            return False

        try:
            reg_num = self._resolve_register(dest_reg)

            # Check if register is already being written
            if self.register_status[reg_num].busy:
                writer = self.register_status[reg_num].writing_instruction
                if writer and writer != instruction:
                    logging.debug(f"WAW hazard: both {instruction} and {writer} write to {dest_reg}")
                    self.hazard_counts[HazardType.WAW] += 1
                    return True

        except ValueError:
            pass

        return False

    def check_structural_hazard(self, instruction: Instruction) -> bool:
        """
        Check for structural hazards (resource conflicts).
        
        Args:
            instruction: Instruction to check
            
        Returns:
            True if structural hazard exists
        """
        # Determine required functional unit type
        unit_type = self._get_required_unit_type(instruction)

        # Check if any unit of this type is available
        available = False
        for unit_name, status in self.function_unit_status.items():
            if unit_type in unit_name and not status.busy:
                available = True
                break

        if not available:
            logging.debug(f"Structural hazard: No {unit_type} available for {instruction}")
            self.hazard_counts[HazardType.STRUCTURAL] += 1
            return True

        return False

    def _get_required_unit_type(self, instruction: Instruction) -> str:
        """Determine which functional unit type an instruction needs."""
        opcode = instruction.opcode.upper()

        if opcode in ["FADD", "FSUB", "FMUL", "FDIV"]:
            return "FPU"
        elif opcode in ["LW", "SW", "LB", "LH", "SB", "SH"]:
            return "LSU"
        else:
            return "ALU"

    def is_register_available(self, register: Union[str, int]) -> bool:
        """Check if a register is available (not busy)."""
        try:
            reg_num = self._resolve_register(register)
            return not self.register_status[reg_num].busy
        except ValueError:
            return True  # Unknown registers are considered available

    def is_function_unit_available(self, unit_name: str) -> bool:
        """Check if a functional unit is available."""
        if unit_name not in self.function_unit_status:
            # Unit doesn't exist yet, so it's "available" to be created
            return True

        return not self.function_unit_status[unit_name].busy

    def allocate_register_write(self, register: Union[str, int],
                               instruction: Instruction) -> None:
        """
        Allocate a register for writing.
        
        Args:
            register: Register to allocate
            instruction: Instruction that will write
        """
        try:
            reg_num = self._resolve_register(register)

            self.register_status[reg_num].busy = True
            self.register_status[reg_num].writing_instruction = instruction
            self.register_status[reg_num].last_write_cycle = self.current_cycle

            logging.debug(f"Allocated register {register} for write by {instruction}")

        except ValueError as e:
            logging.warning(f"Cannot allocate register: {e}")

    def allocate_register_read(self, register: Union[str, int],
                              instruction: Instruction) -> None:
        """
        Track register read by an instruction.
        
        Args:
            register: Register being read
            instruction: Instruction reading the register
        """
        try:
            reg_num = self._resolve_register(register)

            if instruction not in self.register_status[reg_num].reading_instructions:
                self.register_status[reg_num].reading_instructions.append(instruction)

            logging.debug(f"Tracked register {register} read by {instruction}")

        except ValueError as e:
            logging.warning(f"Cannot track register read: {e}")

    def deallocate_register(self, register: Union[str, int]) -> None:
        """
        Deallocate a register after write completes.
        
        Args:
            register: Register to deallocate
        """
        try:
            reg_num = self._resolve_register(register)

            self.register_status[reg_num].busy = False
            self.register_status[reg_num].writing_instruction = None

            logging.debug(f"Deallocated register {register}")

        except ValueError as e:
            logging.warning(f"Cannot deallocate register: {e}")

    def remove_register_read(self, register: Union[str, int],
                            instruction: Instruction) -> None:
        """
        Remove register read tracking after instruction completes.
        
        Args:
            register: Register that was read
            instruction: Instruction that read the register
        """
        try:
            reg_num = self._resolve_register(register)

            if instruction in self.register_status[reg_num].reading_instructions:
                self.register_status[reg_num].reading_instructions.remove(instruction)

        except ValueError:
            pass

    def allocate_function_unit(self, unit_name: str, instruction: Instruction,
                              cycles: int = 1) -> None:
        """
        Allocate a functional unit to an instruction.
        
        Args:
            unit_name: Name of the functional unit
            instruction: Instruction using the unit
            cycles: Number of cycles the unit will be busy
        """
        if unit_name not in self.function_unit_status:
            self.function_unit_status[unit_name] = FunctionalUnitStatus()

        self.function_unit_status[unit_name].busy = True
        self.function_unit_status[unit_name].instruction = instruction
        self.function_unit_status[unit_name].remaining_cycles = cycles
        self.function_unit_status[unit_name].result_ready = False

        logging.debug(f"Allocated {unit_name} to {instruction} for {cycles} cycles")

    def deallocate_function_unit(self, unit_name: str) -> None:
        """Deallocate a functional unit."""
        if unit_name in self.function_unit_status:
            self.function_unit_status[unit_name].busy = False
            self.function_unit_status[unit_name].instruction = None

            logging.debug(f"Deallocated {unit_name}")

    def update_cycle(self) -> None:
        """Update scoreboard state for a new cycle."""
        self.current_cycle += 1

        # Update functional unit cycles
        for unit_name, status in self.function_unit_status.items():
            if status.busy and status.remaining_cycles > 0:
                status.remaining_cycles -= 1

                if status.remaining_cycles == 0:
                    status.result_ready = True
                    logging.debug(f"{unit_name} result ready")

    def get_statistics(self) -> Dict[str, Any]:
        """Get scoreboard statistics."""
        busy_registers = sum(1 for r in self.register_status if r.busy)
        busy_units = sum(1 for u in self.function_unit_status.values() if u.busy)

        return {
            'current_cycle': self.current_cycle,
            'busy_registers': busy_registers,
            'register_utilization': (busy_registers / self.num_registers * 100),
            'busy_functional_units': busy_units,
            'total_functional_units': len(self.function_unit_status),
            'hazard_counts': dict(self.hazard_counts),
            'total_hazards': sum(self.hazard_counts.values())
        }

    def visualize_state(self) -> str:
        """
        Create a visual representation of scoreboard state.
        
        Returns:
            ASCII representation of the scoreboard
        """
        lines = ["Scoreboard State:"]
        lines.append("=" * 60)

        # Register status
        lines.append("Registers (busy):")
        busy_regs = []
        for i, status in enumerate(self.register_status):
            if status.busy:
                writer = status.writing_instruction
                busy_regs.append(f"R{i}({writer.opcode if writer else '?'})")

        if busy_regs:
            lines.append("  " + ", ".join(busy_regs))
        else:
            lines.append("  None busy")

        # Functional unit status
        lines.append("\nFunctional Units:")
        for unit_name, status in self.function_unit_status.items():
            if status.busy:
                inst = status.instruction
                lines.append(f"  {unit_name}: {inst.opcode if inst else 'Unknown'} "
                           f"({status.remaining_cycles} cycles left)")
            else:
                lines.append(f"  {unit_name}: Available")

        # Hazard summary
        lines.append("\nHazard Summary:")
        for hazard_type, count in self.hazard_counts.items():
            if count > 0:
                lines.append(f"  {hazard_type.value}: {count}")

        return "\n".join(lines)

    def reset(self) -> None:
        """Reset scoreboard to initial state."""
        for status in self.register_status:
            status.busy = False
            status.writing_instruction = None
            status.reading_instructions.clear()
            status.last_write_cycle = -1

        self.function_unit_status.clear()
        self.active_instructions.clear()
        self.instruction_dependencies.clear()

        for hazard_type in self.hazard_counts:
            self.hazard_counts[hazard_type] = 0

        self.current_cycle = 0

        logging.info("Scoreboard reset")
