#!/usr/bin/env python3
"""
Test suite for Register Renaming implementations.

Tests cover both register renaming systems:
- AdvancedRegisterRenaming: rename_instruction(id, src_regs, dst_reg)
- EnhancedRegisterRenaming: rename_instruction(instruction) with ROB support
"""

import pytest

from src.register_file.enhanced_register_renaming import EnhancedRegisterRenaming
from src.register_file.register_renaming import AdvancedRegisterRenaming
from src.utils.instruction import Instruction

# ============================== Fixtures ====================================


@pytest.fixture
def advanced_renaming() -> AdvancedRegisterRenaming:
    """Create an AdvancedRegisterRenaming instance."""
    return AdvancedRegisterRenaming(
        num_logical_regs=32,
        num_physical_regs=128,
        reorder_buffer_size=64,
    )


@pytest.fixture
def enhanced_renaming() -> EnhancedRegisterRenaming:
    """Create an EnhancedRegisterRenaming instance."""
    return EnhancedRegisterRenaming(
        config={
            "arch_registers": 32,
            "physical_registers": 128,
            "rob_size": 64,
        }
    )


@pytest.fixture
def add_instruction() -> Instruction:
    """ADD $t0, $t1, $t2."""
    return Instruction(address=0x1000, opcode="add", operands=["$t0", "$t1", "$t2"])


# ===================== AdvancedRegisterRenaming ============================


class TestAdvancedRegisterRenaming:
    """Advanced register renaming with explicit src/dst registers."""

    def test_instantiation(self, advanced_renaming: AdvancedRegisterRenaming) -> None:
        """Should instantiate successfully."""
        assert advanced_renaming is not None

    def test_rename_instruction(
        self, advanced_renaming: AdvancedRegisterRenaming
    ) -> None:
        """Rename an instruction's registers."""
        success, phys_srcs, phys_dst = advanced_renaming.rename_instruction(
            instruction_id=1, src_regs=[1, 2], dst_reg=3
        )
        assert success is True
        assert isinstance(phys_srcs, list)
        assert len(phys_srcs) == 2

    def test_rename_instruction_batch(
        self, advanced_renaming: AdvancedRegisterRenaming
    ) -> None:
        """Rename multiple instructions in a batch."""
        instructions = [
            (1, [1, 2], 3),
            (2, [3, 4], 5),
            (3, [5, 6], 7),
        ]
        results = advanced_renaming.rename_instruction_batch(instructions)
        assert isinstance(results, list)
        assert len(results) == 3

    def test_complete_instruction(
        self, advanced_renaming: AdvancedRegisterRenaming
    ) -> None:
        """Mark an instruction as complete."""
        advanced_renaming.rename_instruction(1, [1, 2], 3)
        advanced_renaming.complete_instruction(1)
        # No exception means success

    def test_commit_instructions(
        self, advanced_renaming: AdvancedRegisterRenaming
    ) -> None:
        """Commit completed instructions."""
        advanced_renaming.rename_instruction(1, [1, 2], 3)
        advanced_renaming.complete_instruction(1)
        advanced_renaming.commit_instructions()
        # No exception means success

    def test_handle_branch_misprediction(
        self, advanced_renaming: AdvancedRegisterRenaming
    ) -> None:
        """Handle branch misprediction by restoring state."""
        advanced_renaming.rename_instruction(1, [1, 2], 3)
        advanced_renaming.handle_branch_misprediction(branch_instruction_id=1)
        # No exception means success

    def test_create_and_restore_checkpoint(
        self, advanced_renaming: AdvancedRegisterRenaming
    ) -> None:
        """Create and restore a checkpoint for speculative execution."""
        checkpoint = advanced_renaming.create_checkpoint(branch_instruction_id=1)
        assert checkpoint is not None

        advanced_renaming.rename_instruction(2, [1, 2], 3)
        advanced_renaming.restore_checkpoint(checkpoint)
        # State should be restored


# ===================== EnhancedRegisterRenaming ============================


class TestEnhancedRegisterRenaming:
    """Enhanced register renaming with ROB support."""

    def test_instantiation(self, enhanced_renaming: EnhancedRegisterRenaming) -> None:
        """Should instantiate successfully."""
        assert enhanced_renaming is not None

    def test_rename_instruction(
        self, enhanced_renaming: EnhancedRegisterRenaming, add_instruction: Instruction
    ) -> None:
        """Rename an instruction and get a ROB ID."""
        add_instruction.destination = "$t0"
        rob_id = enhanced_renaming.rename_instruction(add_instruction)
        assert rob_id is None or isinstance(rob_id, int)

    def test_issue_instructions(
        self, enhanced_renaming: EnhancedRegisterRenaming
    ) -> None:
        """Issue instructions from the queue."""
        enhanced_renaming.issue_instructions()
        # No exception means success

    def test_complete_instruction(
        self, enhanced_renaming: EnhancedRegisterRenaming, add_instruction: Instruction
    ) -> None:
        """Complete an instruction in the ROB."""
        add_instruction.destination = "$t0"
        rob_id = enhanced_renaming.rename_instruction(add_instruction)
        if rob_id is not None:
            enhanced_renaming.complete_instruction(rob_id, result=42, exception=None)

    def test_commit_instructions(
        self, enhanced_renaming: EnhancedRegisterRenaming
    ) -> None:
        """Commit instructions from the ROB."""
        enhanced_renaming.commit_instructions()
        # No exception means success

    def test_handle_branch_misprediction(
        self, enhanced_renaming: EnhancedRegisterRenaming, add_instruction: Instruction
    ) -> None:
        """Handle branch misprediction by flushing ROB entries."""
        add_instruction.destination = "$t0"
        rob_id = enhanced_renaming.rename_instruction(add_instruction)
        if rob_id is not None:
            enhanced_renaming.handle_branch_misprediction(rob_id)

    def test_rename_allocates_rob_entry(
        self, enhanced_renaming: EnhancedRegisterRenaming
    ) -> None:
        """Renaming should allocate a ROB entry and increment count."""
        inst = Instruction(address=0x1000, opcode="add", operands=["$t0", "$t1", "$t2"])
        assert enhanced_renaming.rob_count == 0
        rob_id = enhanced_renaming.rename_instruction(inst)
        assert rob_id == 0
        assert enhanced_renaming.rob_count == 1
        assert enhanced_renaming.rob[0] is not None
        assert enhanced_renaming.rob[0].instruction is inst

    def test_rename_multiple_instructions(
        self, enhanced_renaming: EnhancedRegisterRenaming
    ) -> None:
        """Multiple renames should allocate sequential ROB entries."""
        inst1 = Instruction(
            address=0x1000, opcode="add", operands=["$t0", "$t1", "$t2"]
        )
        inst2 = Instruction(
            address=0x1004, opcode="sub", operands=["$t3", "$t4", "$t5"]
        )
        rob1 = enhanced_renaming.rename_instruction(inst1)
        rob2 = enhanced_renaming.rename_instruction(inst2)
        assert rob1 == 0
        assert rob2 == 1
        assert enhanced_renaming.rob_count == 2

    def test_complete_and_commit_flow(
        self, enhanced_renaming: EnhancedRegisterRenaming
    ) -> None:
        """Full rename → complete → commit flow should free the ROB entry."""
        inst = Instruction(address=0x1000, opcode="add", operands=["$t0", "$t1", "$t2"])
        rob_id = enhanced_renaming.rename_instruction(inst)
        assert rob_id is not None

        # Complete with a result
        ok = enhanced_renaming.complete_instruction(rob_id, result=42, exception=None)
        assert ok is True
        assert enhanced_renaming.rob[rob_id].ready is True
        assert enhanced_renaming.rob[rob_id].result == 42

        # Commit should drain the ROB
        committed = enhanced_renaming.commit_instructions()
        assert rob_id in committed
        assert enhanced_renaming.rob_count == 0

    def test_rob_stall_when_full(
        self, enhanced_renaming: EnhancedRegisterRenaming
    ) -> None:
        """When ROB is full, rename should return None (stall)."""
        # Fill the ROB (size=64)
        for i in range(64):
            inst = Instruction(
                address=i * 4, opcode="add", operands=["$t0", "$t1", "$t2"]
            )
            result = enhanced_renaming.rename_instruction(inst)
            assert result is not None

        # Next rename should stall
        overflow = Instruction(
            address=0x2000, opcode="add", operands=["$t0", "$t1", "$t2"]
        )
        assert enhanced_renaming.rename_instruction(overflow) is None
        assert enhanced_renaming.stats["rob_stalls"] >= 1

    def test_physical_register_allocation(
        self, enhanced_renaming: EnhancedRegisterRenaming
    ) -> None:
        """Each rename with a destination should consume a physical register."""
        initial_free = len(enhanced_renaming.free_list)
        inst = Instruction(address=0x1000, opcode="add", operands=["$t0", "$t1", "$t2"])
        rob_id = enhanced_renaming.rename_instruction(inst)
        assert rob_id is not None
        # One physical register should have been allocated
        assert len(enhanced_renaming.free_list) == initial_free - 1

    def test_branch_misprediction_squashes_younger(
        self, enhanced_renaming: EnhancedRegisterRenaming
    ) -> None:
        """Branch misprediction should squash instructions after the branch."""
        # Rename 3 instructions
        inst1 = Instruction(
            address=0x1000, opcode="add", operands=["$t0", "$t1", "$t2"]
        )
        inst2 = Instruction(address=0x1004, opcode="beq", operands=["$t0", "$t1", 8])
        inst3 = Instruction(
            address=0x1008, opcode="sub", operands=["$t3", "$t4", "$t5"]
        )
        enhanced_renaming.rename_instruction(inst1)  # rob_id=0
        branch_rob = enhanced_renaming.rename_instruction(inst2)  # rob_id=1
        enhanced_renaming.rename_instruction(inst3)  # rob_id=2
        assert enhanced_renaming.rob_count == 3

        # Mispredict on branch (rob_id=1) → squashes rob_id=2
        squashed = enhanced_renaming.handle_branch_misprediction(branch_rob)
        assert squashed == 1
        assert enhanced_renaming.rob_count == 2
        assert enhanced_renaming.stats["branch_mispredictions"] == 1

    def test_stats_tracking(self, enhanced_renaming: EnhancedRegisterRenaming) -> None:
        """Statistics should accurately track rename/complete/commit counts."""
        inst = Instruction(address=0x1000, opcode="add", operands=["$t0", "$t1", "$t2"])
        rob_id = enhanced_renaming.rename_instruction(inst)
        assert enhanced_renaming.stats["instructions_renamed"] == 1

        enhanced_renaming.complete_instruction(rob_id, result=0, exception=None)
        assert enhanced_renaming.stats["instructions_completed"] == 1

        enhanced_renaming.commit_instructions()
        assert enhanced_renaming.stats["instructions_committed"] == 1
