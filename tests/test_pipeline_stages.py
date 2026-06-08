#!/usr/bin/env python3
"""
Test suite for Pipeline Stage implementations.

Tests cover FetchStage, DecodeStage, IssueStage, ExecuteStage,
MemoryAccessStage, WriteBackStage, and ReorderBuffer.
"""

import pytest

from src.cache.cache import DataCache, InstructionCache, Memory
from src.pipeline.decode_stage import DecodeStage
from src.pipeline.execute_stage import ExecuteStage, OutOfOrderExecuteStage
from src.pipeline.memory_access_stage import (
    AdvancedMemoryAccessStage,
    MemoryAccessStage,
)
from src.pipeline.write_back_stage import (
    AdvancedWriteBackStage,
    ReorderBuffer,
    WriteBackStage,
)
from src.register_file.register_file import RegisterFile
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
def add_instruction() -> Instruction:
    return Instruction(address=0x1000, opcode="add", operands=["$t0", "$t1", "$t2"])


# ============================ DecodeStage ===================================


class TestDecodeStage:
    """Decode stage: instruction decoding, operand reading, hazard detection."""

    def test_instantiation(self, reg_file: RegisterFile) -> None:
        decode = DecodeStage(reg_file)
        assert decode is not None

    def test_decode_instruction(
        self, reg_file: RegisterFile, add_instruction: Instruction
    ) -> None:
        decode = DecodeStage(reg_file)
        decoded = decode.decode_instruction(add_instruction)
        assert decoded is not None

    def test_decode_list(
        self, reg_file: RegisterFile, add_instruction: Instruction
    ) -> None:
        decode = DecodeStage(reg_file)
        decoded = decode.decode([add_instruction])
        assert isinstance(decoded, list)

    def test_read_operands(
        self, reg_file: RegisterFile, add_instruction: Instruction
    ) -> None:
        decode = DecodeStage(reg_file)
        decode.read_operands(add_instruction)
        assert hasattr(add_instruction, "register_values")

    def test_hazard_detection(self, reg_file: RegisterFile) -> None:
        decode = DecodeStage(reg_file)
        inst1 = Instruction(
            address=0x1000, opcode="add", operands=["$t0", "$t1", "$t2"]
        )
        inst2 = Instruction(
            address=0x1004, opcode="sub", operands=["$t3", "$t0", "$t4"]
        )
        inst1.destination = "$t0"
        has_hazard = decode.check_hazards(inst2, [inst1])
        assert has_hazard is True

    def test_get_statistics(self, reg_file: RegisterFile) -> None:
        decode = DecodeStage(reg_file)
        stats = decode.get_statistics()
        assert "decoded_instructions" in stats
        assert "stall_cycles" in stats

    def test_reset(self, reg_file: RegisterFile) -> None:
        decode = DecodeStage(reg_file)
        decode.reset()
        assert decode.decoded_count == 0

    def test_invalid_register_file_raises(self) -> None:
        with pytest.raises(TypeError):
            DecodeStage("not a register file")  # type: ignore[arg-type]


# ============================ ExecuteStage ==================================


class TestExecuteStage:
    """Execute stage with ALU, FPU, LSU functional units."""

    def test_instantiation(
        self, reg_file: RegisterFile, data_cache: DataCache, memory: Memory
    ) -> None:
        execute = ExecuteStage(
            num_alu_units=2,
            num_fpu_units=1,
            num_lsu_units=1,
            register_file=reg_file,
            data_cache=data_cache,
            memory=memory,
        )
        assert execute is not None
        assert len(execute.functional_units) == 4  # 2 ALU + 1 FPU + 1 LSU

    def test_find_free_functional_unit(
        self, reg_file: RegisterFile, data_cache: DataCache, memory: Memory
    ) -> None:
        execute = ExecuteStage(
            num_alu_units=2,
            num_fpu_units=0,
            num_lsu_units=0,
            register_file=reg_file,
            data_cache=data_cache,
            memory=memory,
        )
        unit = execute.find_free_functional_unit("ADD")
        assert unit is not None

    def test_get_statistics(
        self, reg_file: RegisterFile, data_cache: DataCache, memory: Memory
    ) -> None:
        execute = ExecuteStage(
            num_alu_units=1,
            num_fpu_units=0,
            num_lsu_units=0,
            register_file=reg_file,
            data_cache=data_cache,
            memory=memory,
        )
        stats = execute.get_statistics()
        assert "executed_instructions" in stats


class TestOutOfOrderExecuteStage:
    """Out-of-order execute stage with instruction window."""

    def test_instantiation(
        self, reg_file: RegisterFile, data_cache: DataCache, memory: Memory
    ) -> None:
        ooo = OutOfOrderExecuteStage(
            num_alu_units=2,
            num_fpu_units=1,
            num_lsu_units=1,
            register_file=reg_file,
            data_cache=data_cache,
            memory=memory,
            window_size=16,
        )
        assert ooo is not None
        assert ooo.window_size == 16

    def test_get_window_status(
        self, reg_file: RegisterFile, data_cache: DataCache, memory: Memory
    ) -> None:
        ooo = OutOfOrderExecuteStage(
            num_alu_units=1,
            num_fpu_units=0,
            num_lsu_units=0,
            register_file=reg_file,
            data_cache=data_cache,
            memory=memory,
            window_size=8,
        )
        status = ooo.get_window_status()
        assert status["window_size"] == 8
        assert status["current_occupancy"] == 0


# ======================== MemoryAccessStage =================================


class TestMemoryAccessStage:
    """Memory access stage: loads, stores, cache access."""

    def test_instantiation(self, data_cache: DataCache, memory: Memory) -> None:
        mem_stage = MemoryAccessStage(data_cache, memory)
        assert mem_stage is not None

    def test_get_statistics(self, data_cache: DataCache, memory: Memory) -> None:
        mem_stage = MemoryAccessStage(data_cache, memory)
        stats = mem_stage.get_statistics()
        assert "load_count" in stats
        assert "cache_hit_rate" in stats

    def test_reset(self, data_cache: DataCache, memory: Memory) -> None:
        mem_stage = MemoryAccessStage(data_cache, memory)
        mem_stage.reset()
        assert mem_stage.load_count == 0


class TestAdvancedMemoryAccessStage:
    """Enhanced memory access with disambiguation and prefetching."""

    def test_instantiation(self, data_cache: DataCache, memory: Memory) -> None:
        adv = AdvancedMemoryAccessStage(data_cache, memory, enable_prefetch=True)
        assert adv is not None
        assert adv.enable_prefetch is True


# ======================== WriteBackStage ====================================


class TestWriteBackStage:
    """Write-back stage: result write-back and port management."""

    def test_instantiation(self, reg_file: RegisterFile) -> None:
        wb = WriteBackStage(reg_file, num_write_ports=2)
        assert wb is not None

    def test_get_statistics(self, reg_file: RegisterFile) -> None:
        wb = WriteBackStage(reg_file)
        stats = wb.get_statistics()
        assert "completed_instructions" in stats

    def test_reset(self, reg_file: RegisterFile) -> None:
        wb = WriteBackStage(reg_file)
        wb.reset()
        assert wb.writeback_count == 0


class TestReorderBuffer:
    """Reorder buffer for in-order commit."""

    def test_instantiation(self) -> None:
        rob = ReorderBuffer(size=32)
        assert rob is not None
        assert rob.size == 32

    def test_allocate_and_commit(self, reg_file: RegisterFile) -> None:
        rob = ReorderBuffer(size=8)
        inst = Instruction(address=0x1000, opcode="add", operands=["$t0", "$t1", "$t2"])
        inst.destination = "$t0"
        rob_id = rob.allocate(inst)
        assert rob_id is not None

        rob.mark_ready(rob_id, result=42)
        committed = rob.commit(reg_file)
        assert len(committed) == 1

    def test_is_full(self) -> None:
        rob = ReorderBuffer(size=2)
        inst1 = Instruction(
            address=0x1000, opcode="add", operands=["$t0", "$t1", "$t2"]
        )
        inst2 = Instruction(
            address=0x1004, opcode="sub", operands=["$t3", "$t4", "$t5"]
        )
        rob.allocate(inst1)
        rob.allocate(inst2)
        assert rob.is_full() is True

    def test_is_empty(self) -> None:
        rob = ReorderBuffer(size=4)
        assert rob.is_empty() is True

    def test_flush(self) -> None:
        rob = ReorderBuffer(size=4)
        inst = Instruction(address=0x1000, opcode="add", operands=["$t0", "$t1", "$t2"])
        rob.allocate(inst)
        rob.flush(starting_from=0)
        assert rob.is_empty() is True


class TestAdvancedWriteBackStage:
    """Enhanced write-back with ROB support."""

    def test_instantiation(self, reg_file: RegisterFile) -> None:
        adv_wb = AdvancedWriteBackStage(reg_file, rob_size=32, num_write_ports=2)
        assert adv_wb is not None
        assert adv_wb.rob is not None

    def test_get_statistics(self, reg_file: RegisterFile) -> None:
        adv_wb = AdvancedWriteBackStage(reg_file, rob_size=16)
        stats = adv_wb.get_statistics()
        assert "rob_occupancy" in stats
        assert "rob_size" in stats
