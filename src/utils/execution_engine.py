#!/usr/bin/env python3

"""
Enhanced Instruction Execution Engine

This module provides cycle-accurate instruction execution with proper
timing models, resource usage, and state management.
"""

from enum import Enum
import logging
from typing import Any, List, Optional

# Handle imports for both package and direct execution
try:
    from .instruction import Instruction, InstructionType
except (ImportError, ValueError):
    import os
    import sys

    sys.path.insert(0, os.path.dirname(__file__))
    from instruction import Instruction, InstructionType  # type: ignore[no-redef]


class ExecutionResult(Enum):
    """Execution result status."""

    SUCCESS = "success"
    STALL = "stall"
    EXCEPTION = "exception"
    BRANCH_TAKEN = "branch_taken"
    BRANCH_NOT_TAKEN = "branch_not_taken"


class ExecutionState:
    """Represents the execution state of an instruction."""

    def __init__(self, instruction: Instruction):
        self.instruction = instruction
        self.cycles_remaining = instruction.latency
        self.started_cycle = -1
        self.completed_cycle = -1
        self.result_value: int | None = None
        self.memory_address: int | None = None
        self.exception: str | None = None
        self.branch_taken: bool = False
        self.branch_target: int | None = None


class CycleAccurateExecutionEngine:
    """
    Cycle-accurate instruction execution engine.

    Provides realistic instruction execution with proper timing,
    resource contention, and state management.
    """

    def __init__(self, register_file, memory, data_cache):
        """
        Initialize the execution engine.

        Args:
            register_file: Register file for operand access
            memory: Main memory system
            data_cache: Data cache for memory operations
        """
        self.register_file = register_file
        self.memory = memory
        self.data_cache = data_cache
        self.logger = logging.getLogger(__name__)

        # Execution state tracking
        self.executing_instructions: dict[int, ExecutionState] = {}
        self.completed_instructions: list[ExecutionState] = []
        self.current_cycle = 0

        # Performance counters
        self.stats = {
            "instructions_executed": 0,
            "cycles_executed": 0,
            "arithmetic_ops": 0,
            "memory_ops": 0,
            "branch_ops": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "pipeline_stalls": 0,
        }

        # Initialize execution handlers
        self._init_execution_handlers()

    def _init_execution_handlers(self) -> None:
        """Initialize instruction execution handlers."""
        self.execution_handlers = {
            InstructionType.ARITHMETIC: self._execute_arithmetic,
            InstructionType.LOGICAL: self._execute_logical,
            InstructionType.COMPARISON: self._execute_comparison,
            InstructionType.LOAD: self._execute_load,
            InstructionType.STORE: self._execute_store,
            InstructionType.BRANCH: self._execute_branch,
            InstructionType.JUMP: self._execute_jump,
            InstructionType.FLOATING_POINT: self._execute_floating_point,
            InstructionType.SYSTEM: self._execute_system,
            InstructionType.NOP: self._execute_nop,
        }

    def start_execution(self, instruction: Instruction, execution_id: int) -> bool:
        """
        Start executing an instruction.

        Args:
            instruction: Instruction to execute
            execution_id: Unique execution identifier

        Returns:
            True if execution started successfully, False if stalled
        """
        if execution_id in self.executing_instructions:
            return False  # Already executing

        # Check resource availability
        if not self._check_resources(instruction):
            self.stats["pipeline_stalls"] += 1
            return False

        # Create execution state
        exec_state = ExecutionState(instruction)
        exec_state.started_cycle = self.current_cycle

        # Start execution
        self.executing_instructions[execution_id] = exec_state

        self.logger.debug(
            f"Started execution of {instruction.opcode} at cycle {self.current_cycle}"
        )
        return True

    def advance_cycle(self) -> list[tuple[int, ExecutionResult, Any]]:
        """
        Advance execution by one cycle.

        Returns:
            List of (execution_id, result, data) tuples for completed instructions
        """
        self.current_cycle += 1
        self.stats["cycles_executed"] += 1
        completed = []

        # Process all executing instructions
        for exec_id, exec_state in list(self.executing_instructions.items()):
            exec_state.cycles_remaining -= 1

            if exec_state.cycles_remaining <= 0:
                # Instruction completed
                result, data = self._complete_execution(exec_state)
                completed.append((exec_id, result, data))

                # Move to completed list
                exec_state.completed_cycle = self.current_cycle
                self.completed_instructions.append(exec_state)
                del self.executing_instructions[exec_id]

                self.stats["instructions_executed"] += 1

        return completed

    def _complete_execution(
        self, exec_state: ExecutionState
    ) -> tuple[ExecutionResult, Any]:
        """
        Complete instruction execution.

        Args:
            exec_state: Execution state to complete

        Returns:
            (result_status, result_data) tuple
        """
        instruction = exec_state.instruction
        handler = self.execution_handlers.get(instruction.instruction_type)  # type: ignore[arg-type]

        if not handler:
            exec_state.exception = (
                f"No handler for instruction type: {instruction.instruction_type}"
            )
            return ExecutionResult.EXCEPTION, exec_state.exception

        try:
            return handler(exec_state)
        except Exception as e:
            exec_state.exception = str(e)
            self.logger.error(f"Execution error for {instruction.opcode}: {e}")
            return ExecutionResult.EXCEPTION, str(e)

    def _execute_arithmetic(
        self, exec_state: ExecutionState
    ) -> tuple[ExecutionResult, Any]:
        """Execute arithmetic instruction."""
        instruction = exec_state.instruction
        self.stats["arithmetic_ops"] += 1

        # Get operand values
        rs_val = self._get_rs_value(instruction)
        rt_val = self._get_rt_value(instruction)
        imm_val = self._get_immediate_value(instruction)

        # Perform operation
        if instruction.opcode == "add":
            result = rs_val + rt_val
        elif instruction.opcode == "addi":
            result = rs_val + imm_val
        elif instruction.opcode == "sub":
            result = rs_val - rt_val
        elif instruction.opcode == "mult":
            result = rs_val * rt_val
            # Store in HI/LO registers (simplified)
            self.register_file.write_register(32, result >> 32)  # HI
            self.register_file.write_register(33, result & 0xFFFFFFFF)  # LO
            return ExecutionResult.SUCCESS, result
        elif instruction.opcode == "div":
            if rt_val == 0:
                exec_state.exception = "Division by zero"
                return ExecutionResult.EXCEPTION, "Division by zero"
            quotient = rs_val // rt_val
            remainder = rs_val % rt_val
            self.register_file.write_register(32, remainder)  # HI
            self.register_file.write_register(33, quotient)  # LO
            return ExecutionResult.SUCCESS, quotient
        elif instruction.opcode == "li":
            result = imm_val
        elif instruction.opcode == "move":
            result = rs_val
        else:
            result = 0  # Default

        # Write result to destination register
        if instruction.destination:
            dest_reg = self._parse_register(instruction.destination)
            self.register_file.write_register(dest_reg, result)
        elif (
            instruction.instruction_type == InstructionType.ARITHMETIC
            and instruction.operands
        ):
            # For R-type: operands = [rd, rs, rt] -> destination is rd
            dest_reg = self._parse_register(instruction.operands[0])  # type: ignore[arg-type]
            self.register_file.write_register(dest_reg, result)

        exec_state.result_value = result
        return ExecutionResult.SUCCESS, result

    def _execute_logical(
        self, exec_state: ExecutionState
    ) -> tuple[ExecutionResult, Any]:
        """Execute logical instruction."""
        instruction = exec_state.instruction

        rs_val = self._get_rs_value(instruction)
        rt_val = self._get_rt_value(instruction)
        imm_val = self._get_immediate_value(instruction)

        if instruction.opcode == "and":
            result = rs_val & rt_val
        elif instruction.opcode == "andi":
            result = rs_val & imm_val
        elif instruction.opcode == "or":
            result = rs_val | rt_val
        elif instruction.opcode == "ori":
            result = rs_val | imm_val
        elif instruction.opcode == "xor":
            result = rs_val ^ rt_val
        elif instruction.opcode == "xori":
            result = rs_val ^ imm_val
        elif instruction.opcode == "nor":
            result = ~(rs_val | rt_val)
        elif instruction.opcode == "sll":
            result = rt_val << (instruction.immediate or 0)  # type: ignore[attr-defined]
        elif instruction.opcode == "srl":
            result = rt_val >> (instruction.immediate or 0)  # type: ignore[attr-defined]
        elif instruction.opcode == "sra":
            result = rt_val >> (
                getattr(instruction, "immediate", 0) or 0
            )  # Arithmetic shift
        elif instruction.opcode == "lui":
            result = imm_val << 16
        else:
            result = 0

        # Write result
        if instruction.rd is not None:  # type: ignore[attr-defined]
            self.register_file.write_register(instruction.rd, result)  # type: ignore[attr-defined]
        elif instruction.rt is not None:  # type: ignore[attr-defined]
            self.register_file.write_register(instruction.rt, result)  # type: ignore[attr-defined]

        exec_state.result_value = result
        return ExecutionResult.SUCCESS, result

    def _execute_comparison(
        self, exec_state: ExecutionState
    ) -> tuple[ExecutionResult, Any]:
        """Execute comparison instruction."""
        instruction = exec_state.instruction

        rs_val = self._get_rs_value(instruction)
        rt_val = self._get_rt_value(instruction)
        imm_val = self._get_immediate_value(instruction)

        if instruction.opcode == "slt":
            result = 1 if rs_val < rt_val else 0
        elif instruction.opcode == "slti":
            result = 1 if rs_val < imm_val else 0
        elif instruction.opcode == "sltu":
            result = 1 if (rs_val & 0xFFFFFFFF) < (rt_val & 0xFFFFFFFF) else 0
        elif instruction.opcode == "sltiu":
            result = 1 if (rs_val & 0xFFFFFFFF) < (imm_val & 0xFFFFFFFF) else 0
        else:
            result = 0

        if instruction.rd is not None:  # type: ignore[attr-defined]
            self.register_file.write_register(instruction.rd, result)  # type: ignore[attr-defined]

        exec_state.result_value = result
        return ExecutionResult.SUCCESS, result

    def _execute_load(self, exec_state: ExecutionState) -> tuple[ExecutionResult, Any]:
        """Execute load instruction."""
        instruction = exec_state.instruction
        self.stats["memory_ops"] += 1

        # Calculate memory address
        base_addr = self._get_rs_value(instruction)
        offset = self._get_immediate_value(instruction)
        address = base_addr + offset

        exec_state.memory_address = address

        # Perform memory access through cache
        try:
            if instruction.opcode == "lw":
                data = self._load_word(address)
            elif instruction.opcode == "lh":
                data = self._load_halfword(address, signed=True)
            elif instruction.opcode == "lhu":
                data = self._load_halfword(address, signed=False)
            elif instruction.opcode == "lb":
                data = self._load_byte(address, signed=True)
            elif instruction.opcode == "lbu":
                data = self._load_byte(address, signed=False)
            else:
                data = 0

            # Write to destination register
            if instruction.rt is not None:  # type: ignore[attr-defined]
                self.register_file.write_register(instruction.rt, data)  # type: ignore[attr-defined]

            exec_state.result_value = data
            return ExecutionResult.SUCCESS, data

        except Exception as e:
            exec_state.exception = f"Memory access error: {e}"
            return ExecutionResult.EXCEPTION, str(e)

    def _execute_store(self, exec_state: ExecutionState) -> tuple[ExecutionResult, Any]:
        """Execute store instruction."""
        instruction = exec_state.instruction
        self.stats["memory_ops"] += 1

        # Calculate memory address
        base_addr = self._get_rs_value(instruction)
        offset = self._get_immediate_value(instruction)
        address = base_addr + offset

        # Get data to store
        data = self._get_rt_value(instruction)

        exec_state.memory_address = address
        exec_state.result_value = data

        # Perform memory access through cache
        try:
            if instruction.opcode == "sw":
                self._store_word(address, data)
            elif instruction.opcode == "sh":
                self._store_halfword(address, data)
            elif instruction.opcode == "sb":
                self._store_byte(address, data)

            return ExecutionResult.SUCCESS, data

        except Exception as e:
            exec_state.exception = f"Memory access error: {e}"
            return ExecutionResult.EXCEPTION, str(e)

    def _execute_branch(
        self, exec_state: ExecutionState
    ) -> tuple[ExecutionResult, Any]:
        """Execute branch instruction."""
        instruction = exec_state.instruction
        self.stats["branch_ops"] += 1

        rs_val = self._get_rs_value(instruction)
        rt_val = self._get_rt_value(instruction)

        # Evaluate branch condition
        taken = False
        if instruction.opcode == "beq":
            taken = rs_val == rt_val
        elif instruction.opcode == "bne":
            taken = rs_val != rt_val
        elif instruction.opcode == "blez":
            taken = rs_val <= 0
        elif instruction.opcode == "bgtz":
            taken = rs_val > 0
        elif instruction.opcode == "bltz":
            taken = rs_val < 0
        elif instruction.opcode == "bgez":
            taken = rs_val >= 0

        exec_state.branch_taken = taken

        if taken:
            # Calculate branch target
            target = instruction.pc + 4 + (instruction.immediate * 4)  # type: ignore[attr-defined]
            exec_state.branch_target = target
            return ExecutionResult.BRANCH_TAKEN, target
        else:
            return ExecutionResult.BRANCH_NOT_TAKEN, instruction.pc + 4  # type: ignore[attr-defined]

    def _execute_jump(self, exec_state: ExecutionState) -> tuple[ExecutionResult, Any]:
        """Execute jump instruction."""
        instruction = exec_state.instruction

        if instruction.opcode == "j":
            target = instruction.immediate  # type: ignore[attr-defined]
        elif instruction.opcode == "jal":
            # Save return address
            self.register_file.write_register(31, instruction.address + 8)  # $ra
            target = self._get_immediate_value(instruction)
        elif instruction.opcode == "jr":
            target = self._get_rs_value(instruction)
        elif instruction.opcode == "jalr":
            # Save return address
            if len(instruction.operands) > 1:
                rd_reg = self._parse_register(instruction.operands[1])  # type: ignore[arg-type]
                self.register_file.write_register(rd_reg, instruction.address + 8)
            target = self._get_rs_value(instruction)
        else:
            target = instruction.address + 4

        exec_state.branch_target = target
        return ExecutionResult.BRANCH_TAKEN, target

    def _execute_floating_point(
        self, exec_state: ExecutionState
    ) -> tuple[ExecutionResult, Any]:
        """Execute floating point instruction (simplified)."""
        # Simplified floating point execution
        # In a real implementation, this would handle IEEE 754 arithmetic
        result = 0.0
        exec_state.result_value = result  # type: ignore[assignment]
        return ExecutionResult.SUCCESS, result

    def _execute_system(
        self, exec_state: ExecutionState
    ) -> tuple[ExecutionResult, Any]:
        """Execute system instruction."""
        instruction = exec_state.instruction

        if instruction.opcode == "syscall":
            # Handle system call based on $v0 register
            syscall_num = self._get_register_value(2)  # $v0

            if syscall_num == 1:  # print integer
                value = self._get_register_value(4)  # $a0
                self.logger.info(f"SYSCALL: print_int({value})")
            elif syscall_num == 10:  # exit
                self.logger.info("SYSCALL: exit")
                return ExecutionResult.SUCCESS, "exit"

            return ExecutionResult.SUCCESS, syscall_num

        return ExecutionResult.SUCCESS, 0

    def _execute_nop(self, exec_state: ExecutionState) -> tuple[ExecutionResult, Any]:
        """Execute NOP instruction."""
        return ExecutionResult.SUCCESS, 0

    def _check_resources(self, instruction: Instruction) -> bool:
        """Check if resources are available for instruction execution."""
        # Simplified resource checking
        # In a real implementation, this would check functional unit availability
        return len(self.executing_instructions) < 4  # Max 4 concurrent executions

    def _get_rs_value(self, instruction: Instruction) -> int:
        """Get RS register value from instruction operands."""
        if (
            instruction.instruction_type == InstructionType.ARITHMETIC
            and len(instruction.operands) >= 3
        ):
            # R-type: operands = [rd, rs, rt] -> rs is operands[1]
            return self._get_register_value(
                self._parse_register(instruction.operands[1])  # type: ignore[arg-type]
            )
        elif instruction.instruction_type in [
            InstructionType.LOAD,
            InstructionType.STORE,
        ]:
            # Memory: operands = [rt, "offset(rs)"] -> extract rs from operands[1]
            if len(instruction.operands) >= 2 and "(" in instruction.operands[1]:  # type: ignore[operator]
                rs_part = instruction.operands[1].split("(")[1].rstrip(")")  # type: ignore[union-attr]
                return self._get_register_value(self._parse_register(rs_part))
        elif (
            instruction.instruction_type == InstructionType.BRANCH
            and len(instruction.operands) >= 1
        ):
            # Branch: operands = [rs, rt, target] -> rs is operands[0]
            return self._get_register_value(
                self._parse_register(instruction.operands[0])  # type: ignore[arg-type]
            )
        return 0

    def _get_rt_value(self, instruction: Instruction) -> int:
        """Get RT register value from instruction operands."""
        if (
            instruction.instruction_type == InstructionType.ARITHMETIC
            and len(instruction.operands) >= 3
        ):
            # R-type: operands = [rd, rs, rt] -> rt is operands[2]
            return self._get_register_value(
                self._parse_register(instruction.operands[2])  # type: ignore[arg-type]
            )
        elif (
            instruction.instruction_type == InstructionType.BRANCH
            and len(instruction.operands) >= 2
        ):
            # Branch: operands = [rs, rt, target] -> rt is operands[1]
            return self._get_register_value(
                self._parse_register(instruction.operands[1])  # type: ignore[arg-type]
            )
        return 0

    def _get_immediate_value(self, instruction: Instruction) -> int:
        """Get immediate value from instruction operands."""
        if (
            instruction.instruction_type == InstructionType.LOAD
            and instruction.opcode.upper() == "LI"
        ):
            # Load immediate: operands = [rt, immediate] -> immediate is operands[1]
            return int(instruction.operands[1]) if len(instruction.operands) >= 2 else 0
        elif instruction.instruction_type in [
            InstructionType.LOAD,
            InstructionType.STORE,
        ]:
            # Memory: operands = [rt, "offset(rs)"] -> extract offset
            if len(instruction.operands) >= 2 and "(" in instruction.operands[1]:  # type: ignore[operator]
                offset_part = instruction.operands[1].split("(")[0]  # type: ignore[union-attr]
                return int(offset_part) if offset_part else 0
        elif (
            instruction.instruction_type == InstructionType.BRANCH
            and len(instruction.operands) >= 3
        ):
            # Branch: operands = [rs, rt, target] -> target is operands[2]
            return int(instruction.operands[2])
        return 0

    def _parse_register(self, reg_str: str) -> int:
        """Parse register string to register number."""
        if reg_str.startswith("$"):
            reg_str = reg_str[1:]

        # Handle named registers
        register_map = {
            "zero": 0,
            "at": 1,
            "v0": 2,
            "v1": 3,
            "a0": 4,
            "a1": 5,
            "a2": 6,
            "a3": 7,
            "t0": 8,
            "t1": 9,
            "t2": 10,
            "t3": 11,
            "t4": 12,
            "t5": 13,
            "t6": 14,
            "t7": 15,
            "s0": 16,
            "s1": 17,
            "s2": 18,
            "s3": 19,
            "s4": 20,
            "s5": 21,
            "s6": 22,
            "s7": 23,
            "t8": 24,
            "t9": 25,
            "k0": 26,
            "k1": 27,
            "gp": 28,
            "sp": 29,
            "fp": 30,
            "ra": 31,
        }

        if reg_str in register_map:
            return register_map[reg_str]
        elif reg_str.isdigit():
            return int(reg_str)
        else:
            return 0  # Default to $zero for unknown registers

    def _get_register_value(self, reg_num: int) -> int:
        """Get register value with proper handling of special registers."""
        if reg_num == 0:  # $zero always returns 0
            return 0
        return self.register_file.read_register(reg_num)

    def _load_word(self, address: int) -> int:
        """Load word from memory through cache."""
        # Check cache first
        cache_result = self.data_cache.read(address)
        if cache_result is not None:
            self.stats["cache_hits"] += 1
            return cache_result

        # Cache miss - load from memory
        self.stats["cache_misses"] += 1
        data = self.memory.read_word(address)
        self.data_cache.write(address, data)
        return data

    def _load_halfword(self, address: int, signed: bool = True) -> int:
        """Load halfword from memory."""
        word = self._load_word(address & ~3)
        offset = address & 3
        halfword = (word >> (offset * 8)) & 0xFFFF

        if signed and halfword & 0x8000:
            halfword |= 0xFFFF0000  # Sign extend

        return halfword

    def _load_byte(self, address: int, signed: bool = True) -> int:
        """Load byte from memory."""
        word = self._load_word(address & ~3)
        offset = address & 3
        byte = (word >> (offset * 8)) & 0xFF

        if signed and byte & 0x80:
            byte |= 0xFFFFFF00  # Sign extend

        return byte

    def _store_word(self, address: int, data: int) -> None:
        """Store word to memory through cache."""
        self.data_cache.write(address, data)
        self.memory.write_word(address, data)

    def _store_halfword(self, address: int, data: int) -> None:
        """Store halfword to memory."""
        word = self._load_word(address & ~3)
        offset = address & 3
        mask = 0xFFFF << (offset * 8)
        word = (word & ~mask) | ((data & 0xFFFF) << (offset * 8))
        self._store_word(address & ~3, word)

    def _store_byte(self, address: int, data: int) -> None:
        """Store byte to memory."""
        word = self._load_word(address & ~3)
        offset = address & 3
        mask = 0xFF << (offset * 8)
        word = (word & ~mask) | ((data & 0xFF) << (offset * 8))
        self._store_word(address & ~3, word)

    def get_statistics(self) -> dict[str, Any]:
        """Get execution statistics."""
        stats = self.stats.copy()
        stats["current_cycle"] = self.current_cycle
        stats["instructions_in_flight"] = len(self.executing_instructions)
        stats["ipc"] = stats["instructions_executed"] / max(stats["cycles_executed"], 1)
        return stats
