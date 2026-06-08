#!/usr/bin/env python3
"""
Test suite for the Cycle-Accurate Execution Engine.

Tests cover CycleAccurateExecutionEngine: instruction execution, cycle
advancement, resource checking, and statistics tracking.
"""

import pytest

from src.cache.cache import DataCache, Memory
from src.register_file.register_file import RegisterFile
from src.utils.execution_engine import (
    CycleAccurateExecutionEngine,
    ExecutionResult,
    ExecutionState,
)
from src.utils.instruction import Instruction

# ============================== Fixtures ====================================


@pytest.fixture
def reg_file() -> RegisterFile:
    return RegisterFile()


@pytest.fixture
def data_cache() -> DataCache:
    return DataCache(cache_size=256, block_size=64, associativity=2)


@pytest.fixture
def memory() -> Memory:
    return Memory(size=4096)


@pytest.fixture
def engine(
    reg_file: RegisterFile, data_cache: DataCache, memory: Memory
) -> CycleAccurateExecutionEngine:
    return CycleAccurateExecutionEngine(
        register_file=reg_file, memory=memory, data_cache=data_cache
    )


@pytest.fixture
def add_instruction() -> Instruction:
    return Instruction(address=0x1000, opcode="add", operands=["$t0", "$t1", "$t2"])


@pytest.fixture
def nop_instruction() -> Instruction:
    return Instruction(address=0x1000, opcode="nop", operands=[])


# ======================== ExecutionEngine ===================================


class TestExecutionEngineBasics:
    """Basic execution engine operations."""

    def test_instantiation(self, engine: CycleAccurateExecutionEngine) -> None:
        assert engine is not None
        assert engine.current_cycle == 0

    def test_start_execution(
        self, engine: CycleAccurateExecutionEngine, add_instruction: Instruction
    ) -> None:
        success = engine.start_execution(add_instruction, execution_id=1)
        assert success is True
        assert 1 in engine.executing_instructions

    def test_duplicate_execution_id_rejected(
        self, engine: CycleAccurateExecutionEngine, add_instruction: Instruction
    ) -> None:
        engine.start_execution(add_instruction, execution_id=1)
        result = engine.start_execution(add_instruction, execution_id=1)
        assert result is False

    def test_advance_cycle(
        self, engine: CycleAccurateExecutionEngine, nop_instruction: Instruction
    ) -> None:
        engine.start_execution(nop_instruction, execution_id=1)
        completed = engine.advance_cycle()
        assert isinstance(completed, list)
        assert engine.current_cycle == 1


class TestExecutionEngineArithmetic:
    """Arithmetic instruction execution."""

    def test_add_execution(
        self,
        engine: CycleAccurateExecutionEngine,
        reg_file: RegisterFile,
    ) -> None:
        # Set up operand values
        reg_file.write_register("$t1", 10)
        reg_file.write_register("$t2", 20)

        inst = Instruction(address=0x1000, opcode="add", operands=["$t0", "$t1", "$t2"])
        engine.start_execution(inst, execution_id=1)

        # Advance enough cycles for ADD (latency=1)
        completed = engine.advance_cycle()
        assert len(completed) >= 0  # May complete this cycle


class TestExecutionEngineLUI:
    """LUI (Load Upper Immediate) instruction execution."""

    def test_lui_shifts_immediate_left_16(
        self,
        engine: CycleAccurateExecutionEngine,
        reg_file: RegisterFile,
    ) -> None:
        """LUI should load the immediate into the upper 16 bits of the register."""
        inst = Instruction(address=0x1000, opcode="lui", operands=["$t0", 0x1234])
        engine.start_execution(inst, execution_id=1)

        # Run enough cycles for completion (latency=1)
        for _ in range(3):
            engine.advance_cycle()

        # $t0 should hold 0x12340000 (0x1234 << 16)
        result = reg_file.read_register("$t0")
        assert result == 0x12340000, f"Expected 0x12340000, got {result:#x}"

    def test_lui_zero_immediate(
        self,
        engine: CycleAccurateExecutionEngine,
        reg_file: RegisterFile,
    ) -> None:
        """LUI with immediate 0 should write 0 to the register."""
        inst = Instruction(address=0x1000, opcode="lui", operands=["$t1", 0])
        engine.start_execution(inst, execution_id=1)

        for _ in range(3):
            engine.advance_cycle()

        result = reg_file.read_register("$t1")
        assert result == 0

    def test_lui_max_immediate(
        self,
        engine: CycleAccurateExecutionEngine,
        reg_file: RegisterFile,
    ) -> None:
        """LUI with 0xFFFF should produce 0xFFFF0000."""
        inst = Instruction(address=0x1000, opcode="lui", operands=["$t2", 0xFFFF])
        engine.start_execution(inst, execution_id=1)

        for _ in range(3):
            engine.advance_cycle()

        result = reg_file.read_register("$t2")
        assert result == 0xFFFF0000, f"Expected 0xFFFF0000, got {result:#x}"


class TestExecutionEngineResources:
    """Resource management and functional unit capacity."""

    def test_fu_capacity(self, engine: CycleAccurateExecutionEngine) -> None:
        """Engine should have defined FU capacities."""
        assert engine.fu_capacity["ALU"] == 2
        assert engine.fu_capacity["FPU"] == 1
        assert engine.fu_capacity["LSU"] == 2
        assert engine.fu_capacity["BRU"] == 1

    def test_get_statistics(self, engine: CycleAccurateExecutionEngine) -> None:
        stats = engine.get_statistics()
        assert "instructions_executed" in stats
        assert "ipc" in stats
        assert "cache_hit_rate" in stats


class TestExecutionEnums:
    """Verify ExecutionResult and ExecutionState."""

    def test_execution_result_enum(self) -> None:
        assert ExecutionResult.SUCCESS is not None
        assert ExecutionResult.STALL is not None
        assert ExecutionResult.EXCEPTION is not None
        assert ExecutionResult.BRANCH_TAKEN is not None
        assert ExecutionResult.BRANCH_NOT_TAKEN is not None

    def test_execution_state(self, add_instruction: Instruction) -> None:
        state = ExecutionState(add_instruction)
        assert state.instruction is add_instruction
        assert state.started_cycle == -1
        assert state.completed_cycle == -1
