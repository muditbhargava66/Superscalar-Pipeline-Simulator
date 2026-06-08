#!/usr/bin/env python3
"""
Test suite for Register File implementations.

Tests cover RegisterFile and PhysicalRegisterFile from register_file.py,
including basic read/write operations, multi-port access, register locking,
and physical register allocation/deallocation.
"""

import pytest

from src.register_file.register_file import PhysicalRegisterFile, RegisterFile

# ============================== Fixtures ====================================


@pytest.fixture
def reg_file() -> RegisterFile:
    """Create a fresh RegisterFile instance."""
    return RegisterFile()


@pytest.fixture
def phys_reg_file() -> PhysicalRegisterFile:
    """Create a fresh PhysicalRegisterFile instance."""
    return PhysicalRegisterFile()


# ============================ RegisterFile ==================================


class TestRegisterFileBasics:
    """Basic read/write operations on the register file."""

    def test_general_registers_initially_zero(self, reg_file: RegisterFile) -> None:
        """General-purpose registers (excluding $gp and $sp) should be zero."""
        # Registers 28 ($gp) and 29 ($sp) have non-zero initial values
        for i in range(32):
            if i in (0, 28, 29):
                continue
            assert reg_file.read_register(i) == 0

    def test_write_and_read(self, reg_file: RegisterFile) -> None:
        """Write a value and verify it can be read back."""
        reg_file.write_register(5, 42)
        assert reg_file.read_register(5) == 42

    def test_write_multiple_registers(self, reg_file: RegisterFile) -> None:
        """Write to multiple registers independently."""
        reg_file.write_register(1, 100)
        reg_file.write_register(2, 200)
        reg_file.write_register(3, 300)
        assert reg_file.read_register(1) == 100
        assert reg_file.read_register(2) == 200
        assert reg_file.read_register(3) == 300

    def test_overwrite_register(self, reg_file: RegisterFile) -> None:
        """Overwriting a register should update its value."""
        reg_file.write_register(10, 50)
        reg_file.write_register(10, 99)
        assert reg_file.read_register(10) == 99

    def test_zero_register_always_zero(self, reg_file: RegisterFile) -> None:
        """Register $zero (index 0) should always return 0."""
        reg_file.write_register(0, 123)
        assert reg_file.read_register(0) == 0

    def test_stack_pointer_initialization(self, reg_file: RegisterFile) -> None:
        """Stack pointer ($sp, register 29) should be initialized to 0x7FFFFFFC."""
        assert reg_file.read_register(29) == 0x7FFFFFFC

    def test_global_pointer_initialization(self, reg_file: RegisterFile) -> None:
        """Global pointer ($gp, register 28) should be initialized to 0x10008000."""
        assert reg_file.read_register(28) == 0x10008000

    def test_named_register_read(self, reg_file: RegisterFile) -> None:
        """Read registers by their MIPS names."""
        reg_file.write_register("$t0", 42)
        assert reg_file.read_register("$t0") == 42

    def test_invalid_register_raises(self, reg_file: RegisterFile) -> None:
        """Accessing an invalid register should raise ValueError."""
        with pytest.raises(ValueError):
            reg_file.read_register(99)


class TestRegisterFileMultiPort:
    """Multi-port read and write operations."""

    def test_read_multiple(self, reg_file: RegisterFile) -> None:
        """Read multiple registers in a single operation."""
        reg_file.write_register(1, 10)
        reg_file.write_register(2, 20)
        reg_file.write_register(3, 30)
        values = reg_file.read_multiple([1, 2, 3])
        assert values == [10, 20, 30]

    def test_write_multiple_respects_port_limit(self, reg_file: RegisterFile) -> None:
        """write_multiple is limited by num_write_ports (default 2)."""
        # Default write_ports = 2, so only first 2 writes should succeed
        reg_file.write_multiple([(1, 100), (2, 200), (3, 300)])
        assert reg_file.read_register(1) == 100
        assert reg_file.read_register(2) == 200
        # Third write may be dropped due to write port conflict
        # (depends on implementation — checking it doesn't crash)

    def test_read_multiple_empty_list(self, reg_file: RegisterFile) -> None:
        """Reading an empty list should return an empty list."""
        assert reg_file.read_multiple([]) == []

    def test_write_multiple_empty_list(self, reg_file: RegisterFile) -> None:
        """Writing an empty list should not raise an error."""
        reg_file.write_multiple([])
        # No exception means success


class TestRegisterFileLocking:
    """Register locking mechanism for pipeline hazard prevention."""

    def test_lock_register(self, reg_file: RegisterFile) -> None:
        """Lock a register and verify via the register_locks list."""
        reg_file.lock_register(5)
        assert reg_file.register_locks[5] is True

    def test_unlock_register(self, reg_file: RegisterFile) -> None:
        """Unlock a previously locked register."""
        reg_file.lock_register(5)
        reg_file.unlock_register(5)
        assert reg_file.register_locks[5] is False

    def test_lock_multiple_registers(self, reg_file: RegisterFile) -> None:
        """Lock multiple registers independently."""
        reg_file.lock_register(1)
        reg_file.lock_register(2)
        reg_file.lock_register(3)
        assert reg_file.register_locks[1] is True
        assert reg_file.register_locks[2] is True
        assert reg_file.register_locks[3] is True
        assert reg_file.register_locks[4] is False


class TestRegisterFileStatistics:
    """Statistics tracking for register file operations."""

    def test_read_count(self, reg_file: RegisterFile) -> None:
        """Track the number of read operations."""
        reg_file.read_register(1)
        reg_file.read_register(2)
        reg_file.read_register(3)
        stats = reg_file.get_statistics()
        assert stats["read_count"] == 3

    def test_write_count(self, reg_file: RegisterFile) -> None:
        """Track the number of write operations."""
        reg_file.write_register(1, 10)
        reg_file.write_register(2, 20)
        stats = reg_file.get_statistics()
        assert stats["write_count"] == 2

    def test_reset_clears_state(self, reg_file: RegisterFile) -> None:
        """Reset should clear all state including statistics."""
        reg_file.read_register(1)
        reg_file.write_register(2, 10)
        reg_file.reset()
        stats = reg_file.get_statistics()
        assert stats["read_count"] == 0
        assert stats["write_count"] == 0

    def test_dump_registers(self, reg_file: RegisterFile) -> None:
        """dump_registers should return a formatted string."""
        reg_file.write_register(1, 42)
        output = reg_file.dump_registers(only_nonzero=True)
        assert isinstance(output, str)


# ======================== PhysicalRegisterFile =============================


class TestPhysicalRegisterFile:
    """Physical register file with register renaming support."""

    def test_initialization(self, phys_reg_file: PhysicalRegisterFile) -> None:
        """Physical register file should initialize with mapping table and free list."""
        assert phys_reg_file.num_physical == 64
        assert phys_reg_file.num_architectural == 32
        assert len(phys_reg_file.mapping_table) == 32
        assert len(phys_reg_file.free_list) == 32  # 64 - 32

    def test_allocate_physical_register(
        self, phys_reg_file: PhysicalRegisterFile
    ) -> None:
        """Allocate a physical register for an architectural register."""
        phys_reg = phys_reg_file.allocate_physical_register(arch_reg=5)
        assert phys_reg is not None
        assert isinstance(phys_reg, int)
        assert phys_reg >= 32  # Should come from the free list (32-63)

    def test_free_physical_register(self, phys_reg_file: PhysicalRegisterFile) -> None:
        """Free a previously allocated physical register."""
        phys_reg = phys_reg_file.allocate_physical_register(arch_reg=5)
        assert phys_reg is not None
        phys_reg_file.free_physical_register(phys_reg)
        assert phys_reg in phys_reg_file.free_list

    def test_multiple_allocations(self, phys_reg_file: PhysicalRegisterFile) -> None:
        """Allocate multiple physical registers from the free list."""
        regs = []
        for arch in range(10):
            reg = phys_reg_file.allocate_physical_register(arch_reg=arch)
            if reg is not None:
                regs.append(reg)
        assert len(regs) == 10
        # All allocated registers should be from the free pool (>= 32)
        assert all(r >= 32 for r in regs)

    def test_exhaust_free_list(self, phys_reg_file: PhysicalRegisterFile) -> None:
        """Exhausting the free list should return None."""
        # Allocate all 32 free physical registers
        for arch in range(32):
            phys_reg_file.allocate_physical_register(arch_reg=arch)
        # Next allocation should fail
        result = phys_reg_file.allocate_physical_register(arch_reg=0)
        assert result is None

    def test_read_architectural(self, phys_reg_file: PhysicalRegisterFile) -> None:
        """Read through the architectural register mapping."""
        # Write to the physical register mapped to arch reg 5
        phys_reg = phys_reg_file.mapping_table[5]
        phys_reg_file.registers[phys_reg] = 99
        assert phys_reg_file.read_architectural(5) == 99

    def test_write_architectural(self, phys_reg_file: PhysicalRegisterFile) -> None:
        """Write through the architectural register mapping."""
        phys_reg_file.write_architectural(10, 777)
        phys_reg = phys_reg_file.mapping_table[10]
        assert phys_reg_file.registers[phys_reg] == 777
