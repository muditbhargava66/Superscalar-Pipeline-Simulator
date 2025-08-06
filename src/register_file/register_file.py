"""
Register File Implementation

This module implements the register file for the superscalar pipeline,
supporting MIPS-style register naming and access.
"""

from __future__ import annotations

import logging
from typing import Any, Optional, Union


class RegisterFile:
    """
    Register file for the processor.
    
    Supports:
    - 32 general-purpose registers (MIPS-style)
    - Named register access ($zero, $t0, etc.)
    - Multiple read/write ports
    - Register locking for WAW hazard prevention
    """

    # MIPS register name mappings
    REGISTER_NAMES = {
        '$zero': 0, '$0': 0,      # Always zero
        '$at': 1, '$1': 1,        # Assembler temporary
        '$v0': 2, '$2': 2,        # Return values
        '$v1': 3, '$3': 3,
        '$a0': 4, '$4': 4,        # Arguments
        '$a1': 5, '$5': 5,
        '$a2': 6, '$6': 6,
        '$a3': 7, '$7': 7,
        '$t0': 8, '$8': 8,        # Temporaries
        '$t1': 9, '$9': 9,
        '$t2': 10, '$10': 10,
        '$t3': 11, '$11': 11,
        '$t4': 12, '$12': 12,
        '$t5': 13, '$13': 13,
        '$t6': 14, '$14': 14,
        '$t7': 15, '$15': 15,
        '$s0': 16, '$16': 16,     # Saved registers
        '$s1': 17, '$17': 17,
        '$s2': 18, '$18': 18,
        '$s3': 19, '$19': 19,
        '$s4': 20, '$20': 20,
        '$s5': 21, '$21': 21,
        '$s6': 22, '$22': 22,
        '$s7': 23, '$23': 23,
        '$t8': 24, '$24': 24,     # More temporaries
        '$t9': 25, '$25': 25,
        '$k0': 26, '$26': 26,     # Kernel reserved
        '$k1': 27, '$27': 27,
        '$gp': 28, '$28': 28,     # Global pointer
        '$sp': 29, '$29': 29,     # Stack pointer
        '$fp': 30, '$30': 30,     # Frame pointer
        '$s8': 30,                # Alternative name for $fp
        '$ra': 31, '$31': 31      # Return address
    }

    def __init__(self, num_registers: int = 32,
                 num_read_ports: int = 4,
                 num_write_ports: int = 2) -> None:
        """
        Initialize the register file.
        
        Args:
            num_registers: Number of registers (default 32 for MIPS)
            num_read_ports: Number of simultaneous read ports
            num_write_ports: Number of simultaneous write ports
        """
        self.num_registers = num_registers
        self.num_read_ports = num_read_ports
        self.num_write_ports = num_write_ports

        # Initialize registers
        self.registers: List[int] = [0] * num_registers

        # Register locks for preventing hazards
        self.register_locks: List[bool] = [False] * num_registers

        # Pending writes (for write port arbitration)
        self.pending_writes: List[tuple] = []

        # Statistics
        self.read_count = 0
        self.write_count = 0
        self.port_conflicts = 0

        # Initialize special registers
        self._initialize_special_registers()

        logging.debug(f"Initialized Register File with {num_registers} registers, "
                     f"{num_read_ports} read ports, {num_write_ports} write ports")

    def _initialize_special_registers(self) -> None:
        """Initialize special registers with default values."""
        # $sp (stack pointer) - typically starts at high memory
        self.registers[29] = 0x7FFFFFFC  # Near top of 2GB address space

        # $gp (global pointer) - typically points to global data area
        self.registers[28] = 0x10008000  # Common MIPS data segment start

        # $zero is handled specially in read/write

    def _resolve_register(self, register: Union[str, int]) -> int:
        """
        Resolve register identifier to register number.
        
        Args:
            register: Register name or number
            
        Returns:
            Register number (0-31)
            
        Raises:
            ValueError: If register is invalid
        """
        if isinstance(register, int):
            if 0 <= register < self.num_registers:
                return register
            else:
                raise ValueError(f"Invalid register number: {register}")

        elif isinstance(register, str):
            # Try MIPS name mapping first
            if register in self.REGISTER_NAMES:
                return self.REGISTER_NAMES[register]

            # Try r<N> format
            if register.startswith('r') and register[1:].isdigit():
                reg_num = int(register[1:])
                if 0 <= reg_num < self.num_registers:
                    return reg_num

            # Try direct number string
            if register.isdigit():
                reg_num = int(register)
                if 0 <= reg_num < self.num_registers:
                    return reg_num

            raise ValueError(f"Invalid register name: {register}")

        else:
            raise TypeError(f"Register must be string or int, not {type(register)}")

    def read_register(self, register: Union[str, int]) -> int:
        """
        Read value from a register.
        
        Args:
            register: Register identifier (name or number)
            
        Returns:
            Register value
        """
        reg_num = self._resolve_register(register)

        # $zero always returns 0
        if reg_num == 0:
            return 0

        self.read_count += 1
        value = self.registers[reg_num]

        logging.debug(f"Read R{reg_num} ({self._get_register_name(reg_num)}) = {value:#x}")

        return value

    def write_register(self, register: Union[str, int], value: Any) -> None:
        """
        Write value to a register.
        
        Args:
            register: Register identifier (name or number)
            value: Value to write
        """
        reg_num = self._resolve_register(register)

        # $zero is read-only
        if reg_num == 0:
            logging.debug("Attempted write to $zero ignored")
            return

        # Convert value to integer if needed
        if not isinstance(value, int):
            try:
                value = int(value)
            except (ValueError, TypeError):
                value = 0
                logging.warning("Invalid value for register write, using 0")

        # Check if register is locked
        if self.register_locks[reg_num]:
            logging.warning(f"Register R{reg_num} is locked, queueing write")
            self.pending_writes.append((reg_num, value))
            return

        self.write_count += 1
        old_value = self.registers[reg_num]
        self.registers[reg_num] = value & 0xFFFFFFFF  # 32-bit register

        logging.debug(f"Write R{reg_num} ({self._get_register_name(reg_num)}) = "
                     f"{value:#x} (was {old_value:#x})")

    def read_multiple(self, registers: List[Union[str, int]]) -> List[int]:
        """
        Read multiple registers (simulating multiple read ports).
        
        Args:
            registers: List of register identifiers
            
        Returns:
            List of register values
            
        Raises:
            ValueError: If too many simultaneous reads requested
        """
        if len(registers) > self.num_read_ports:
            raise ValueError(f"Too many simultaneous reads: {len(registers)} > {self.num_read_ports}")

        return [self.read_register(reg) for reg in registers]

    def write_multiple(self, writes: List[Tuple[Union[str, int], Any]]) -> None:
        """
        Write multiple registers (simulating multiple write ports).
        
        Args:
            writes: List of (register, value) tuples
            
        Raises:
            ValueError: If too many simultaneous writes requested
        """
        if len(writes) > self.num_write_ports:
            self.port_conflicts += 1
            # Only process up to num_write_ports writes
            writes = writes[:self.num_write_ports]
            logging.warning(f"Write port conflict: only processing {self.num_write_ports} writes")

        for register, value in writes:
            self.write_register(register, value)

    def lock_register(self, register: Union[str, int]) -> None:
        """Lock a register to prevent WAW hazards."""
        reg_num = self._resolve_register(register)
        if reg_num != 0:  # Can't lock $zero
            self.register_locks[reg_num] = True
            logging.debug(f"Locked register R{reg_num}")

    def unlock_register(self, register: Union[str, int]) -> None:
        """Unlock a register and process any pending writes."""
        reg_num = self._resolve_register(register)
        if reg_num != 0 and self.register_locks[reg_num]:
            self.register_locks[reg_num] = False
            logging.debug(f"Unlocked register R{reg_num}")

            # Process pending writes for this register
            remaining_writes = []
            for pending_reg, pending_val in self.pending_writes:
                if pending_reg == reg_num:
                    self.write_register(pending_reg, pending_val)
                else:
                    remaining_writes.append((pending_reg, pending_val))

            self.pending_writes = remaining_writes

    def _get_register_name(self, reg_num: int) -> str:
        """Get the canonical name for a register number."""
        # Reverse lookup in REGISTER_NAMES
        for name, num in self.REGISTER_NAMES.items():
            if num == reg_num and not name.startswith('$') and name[1:].isdigit():
                continue  # Skip numeric aliases
            if num == reg_num:
                return name

        return f"r{reg_num}"

    def get_all_registers(self) -> Dict[str, int]:
        """
        Get all register values as a dictionary.
        
        Returns:
            Dictionary mapping register names to values
        """
        result = {}
        for i in range(self.num_registers):
            name = self._get_register_name(i)
            result[name] = self.registers[i]

        return result

    def dump_registers(self, only_nonzero: bool = True) -> str:
        """
        Get a formatted dump of register contents.
        
        Args:
            only_nonzero: Only show non-zero registers
            
        Returns:
            Formatted register dump string
        """
        lines = ["Register File Contents:"]
        lines.append("-" * 50)

        for i in range(0, self.num_registers, 4):
            row = []
            for j in range(4):
                if i + j < self.num_registers:
                    reg_num = i + j
                    value = self.registers[reg_num]

                    if only_nonzero and value == 0 and reg_num != 0:
                        continue

                    name = self._get_register_name(reg_num)
                    row.append(f"{name:>4} = {value:08x}")

            if row:
                lines.append("  ".join(row))

        return "\n".join(lines)

    def get_statistics(self) -> Dict[str, Any]:
        """Get register file statistics."""
        non_zero_regs = sum(1 for v in self.registers[1:] if v != 0)  # Exclude $zero

        return {
            'read_count': self.read_count,
            'write_count': self.write_count,
            'port_conflicts': self.port_conflicts,
            'non_zero_registers': non_zero_regs,
            'locked_registers': sum(self.register_locks),
            'pending_writes': len(self.pending_writes)
        }

    def reset(self) -> None:
        """Reset register file to initial state."""
        self.registers = [0] * self.num_registers
        self.register_locks = [False] * self.num_registers
        self.pending_writes = []
        self.read_count = 0
        self.write_count = 0
        self.port_conflicts = 0

        # Re-initialize special registers
        self._initialize_special_registers()

        logging.info("Register file reset")

    def __str__(self) -> str:
        """String representation showing key registers."""
        key_regs = ['$zero', '$v0', '$a0', '$sp', '$ra']
        values = []
        for reg in key_regs:
            val = self.read_register(reg)
            values.append(f"{reg}={val:#x}")

        return f"RegisterFile({', '.join(values)}, ...)"

    def __repr__(self) -> str:
        """Detailed representation."""
        return (f"RegisterFile(registers={self.num_registers}, "
                f"read_ports={self.num_read_ports}, "
                f"write_ports={self.num_write_ports})")


class PhysicalRegisterFile(RegisterFile):
    """
    Physical register file for register renaming support.
    
    Extends basic register file with:
    - More physical registers than architectural
    - Free list management
    - Register mapping table
    """

    def __init__(self, num_physical: int = 64, num_architectural: int = 32) -> None:
        """
        Initialize physical register file.
        
        Args:
            num_physical: Total number of physical registers
            num_architectural: Number of architectural registers
        """
        super().__init__(num_registers=num_physical)

        self.num_architectural = num_architectural
        self.num_physical = num_physical

        # Mapping from architectural to physical registers
        self.mapping_table: List[int] = list(range(num_architectural))

        # Free list of physical registers
        self.free_list: List[int] = list(range(num_architectural, num_physical))

        # Reverse mapping for debugging
        self.reverse_map: Dict[int, int] = {i: i for i in range(num_architectural)}

        logging.debug(f"Initialized Physical Register File: "
                     f"{num_architectural} architectural, {num_physical} physical")

    def allocate_physical_register(self, arch_reg: int) -> Optional[int]:
        """
        Allocate a physical register for an architectural register.
        
        Args:
            arch_reg: Architectural register number
            
        Returns:
            Physical register number or None if none available
        """
        if not self.free_list:
            logging.warning("No free physical registers available")
            return None

        # Get a free physical register
        phys_reg = self.free_list.pop(0)

        # Update mapping
        old_phys = self.mapping_table[arch_reg]
        self.mapping_table[arch_reg] = phys_reg

        # Update reverse mapping
        if old_phys in self.reverse_map:
            del self.reverse_map[old_phys]
        self.reverse_map[phys_reg] = arch_reg

        logging.debug(f"Mapped architectural R{arch_reg} to physical P{phys_reg}")

        return phys_reg

    def free_physical_register(self, phys_reg: int) -> None:
        """
        Return a physical register to the free list.
        
        Args:
            phys_reg: Physical register to free
        """
        if phys_reg >= self.num_architectural and phys_reg not in self.free_list:
            self.free_list.append(phys_reg)

            if phys_reg in self.reverse_map:
                del self.reverse_map[phys_reg]

            logging.debug(f"Freed physical register P{phys_reg}")

    def read_architectural(self, arch_reg: int) -> int:
        """Read value of an architectural register."""
        if 0 <= arch_reg < self.num_architectural:
            phys_reg = self.mapping_table[arch_reg]
            return self.registers[phys_reg]
        else:
            raise ValueError(f"Invalid architectural register: {arch_reg}")

    def write_architectural(self, arch_reg: int, value: int) -> None:
        """Write value to an architectural register."""
        if 0 <= arch_reg < self.num_architectural:
            phys_reg = self.mapping_table[arch_reg]
            self.registers[phys_reg] = value
        else:
            raise ValueError(f"Invalid architectural register: {arch_reg}")
