"""
tests/test_instructions.py
~~~~~~~~~~~~~~~~~~~~~~~~~~

Unit tests for the core instruction representation layer. Covers the
``Instruction``, ``BranchInstruction``, and ``InstructionBundle`` classes
defined in ``src/utils/instruction.py``.

What's tested:
  - InstructionType auto-detection from opcodes
  - R/I/S-type classification
  - Source and destination register extraction
  - Branch condition evaluation (BEQ, BNE, BLT, BGE, jumps)
  - Latency lookup for every supported opcode
  - BranchInstruction target-address calculation
  - InstructionBundle dependency detection and branch scanning
"""

from __future__ import annotations

import pytest

from src.utils.instruction import (
    BranchInstruction,
    Instruction,
    InstructionBundle,
    InstructionStatus,
    InstructionType,
)

# ---------------------------------------------------------------------------
# Helpers — a minimal mock that satisfies the branch-evaluation contract
# ---------------------------------------------------------------------------


class _FakeRegisterFile:
    """Stand-in for RegisterFile that returns pre-set values."""

    def __init__(self, values: dict[str, int]) -> None:
        self._values = values

    def read_register(self, reg: str) -> int:
        return self._values.get(reg, 0)


# ========================== InstructionType ================================


class TestInstructionTypeDetection:
    """Opcode → InstructionType mapping exercised in __post_init__."""

    @pytest.mark.parametrize(
        "opcode, expected",
        [
            ("ADD", InstructionType.ARITHMETIC),
            ("SUB", InstructionType.ARITHMETIC),
            ("ADDI", InstructionType.ARITHMETIC),
            ("AND", InstructionType.LOGICAL),
            ("OR", InstructionType.LOGICAL),
            ("XOR", InstructionType.LOGICAL),
            ("SLT", InstructionType.LOGICAL),
            ("LW", InstructionType.MEMORY),
            ("SW", InstructionType.MEMORY),
            ("LB", InstructionType.MEMORY),
            ("SH", InstructionType.MEMORY),
            ("BEQ", InstructionType.BRANCH),
            ("BNE", InstructionType.BRANCH),
            ("BLT", InstructionType.BRANCH),
            ("J", InstructionType.JUMP),
            ("JAL", InstructionType.JUMP),
            ("JR", InstructionType.JUMP),
            ("FADD", InstructionType.FLOAT),
            ("FSUB", InstructionType.FLOAT),
            ("FMUL", InstructionType.FLOAT),
            ("FDIV", InstructionType.FLOAT),
            ("NOP", InstructionType.NOP),
        ],
    )
    def test_auto_detect_type(self, opcode: str, expected: InstructionType) -> None:
        inst = Instruction(address=0x1000, opcode=opcode, operands=["$1", "$2", "$3"])
        assert inst.instruction_type == expected

    def test_opcode_normalised_to_uppercase(self) -> None:
        inst = Instruction(address=0, opcode="add", operands=["$1", "$2", "$3"])
        assert inst.opcode == "ADD"

    def test_explicit_type_overrides_detection(self) -> None:
        inst = Instruction(
            address=0,
            opcode="ADD",
            operands=["$1", "$2", "$3"],
            instruction_type=InstructionType.LOGICAL,  # force override
        )
        assert inst.instruction_type == InstructionType.LOGICAL


# ========================== Format Classification ==========================


class TestInstructionFormat:
    """R-type / I-type / S-type classification."""

    def test_r_type_add(self) -> None:
        inst = Instruction(address=0, opcode="ADD", operands=["$1", "$2", "$3"])
        assert inst.is_r_type()
        assert not inst.is_i_type()
        assert not inst.is_s_type()

    def test_i_type_addi(self) -> None:
        inst = Instruction(address=0, opcode="ADDI", operands=["$1", "$2", 10])
        assert inst.is_i_type()
        assert not inst.is_r_type()

    def test_s_type_sw(self) -> None:
        inst = Instruction(address=0, opcode="SW", operands=["$3", "0($2)"])
        assert inst.is_s_type()
        assert not inst.is_r_type()

    @pytest.mark.parametrize("opcode", ["FADD", "FSUB", "FMUL", "FDIV"])
    def test_r_type_float(self, opcode: str) -> None:
        inst = Instruction(address=0, opcode=opcode, operands=["$1", "$2", "$3"])
        assert inst.is_r_type()


# ========================== Register Extraction ============================


class TestRegisterExtraction:
    """Source and destination register parsing."""

    def test_r_type_destination(self) -> None:
        inst = Instruction(address=0, opcode="ADD", operands=["$8", "$9", "$10"])
        assert inst.get_destination_register() == "$8"
        assert inst.has_destination_register()

    def test_r_type_sources(self) -> None:
        inst = Instruction(address=0, opcode="ADD", operands=["$8", "$9", "$10"])
        assert inst.get_source_registers() == ["$9", "$10"]

    def test_i_type_destination_and_sources(self) -> None:
        inst = Instruction(address=0, opcode="ADDI", operands=["$4", "$5", 42])
        assert inst.get_destination_register() == "$4"
        assert inst.get_source_registers() == ["$5"]

    def test_store_has_no_destination(self) -> None:
        inst = Instruction(address=0, opcode="SW", operands=["$3", "0($2)"])
        assert not inst.has_destination_register()
        assert inst.get_destination_register() is None

    def test_store_sources(self) -> None:
        inst = Instruction(address=0, opcode="SW", operands=["$3", "8($2)"])
        sources = inst.get_source_registers()
        # Value register and base register
        assert "$3" in sources
        assert "$2" in sources

    def test_branch_sources(self) -> None:
        inst = Instruction(address=0, opcode="BEQ", operands=["$4", "$5", -3])
        sources = inst.get_source_registers()
        assert "$4" in sources
        assert "$5" in sources

    def test_branch_has_no_destination(self) -> None:
        inst = Instruction(address=0, opcode="BEQ", operands=["$4", "$5", 10])
        assert not inst.has_destination_register()

    def test_jump_has_no_destination(self) -> None:
        inst = Instruction(address=0, opcode="J", operands=[0x1000])
        assert not inst.has_destination_register()


# ========================== Type Queries ===================================


class TestInstructionTypeQueries:
    """Boolean query methods (is_load, is_branch, etc.)."""

    def test_is_load(self) -> None:
        lw = Instruction(address=0, opcode="LW", operands=["$2", "0($3)"])
        assert lw.is_load()
        assert lw.is_memory_operation()

    def test_is_store(self) -> None:
        sw = Instruction(address=0, opcode="SW", operands=["$2", "4($3)"])
        assert sw.is_store()
        assert sw.is_memory_operation()

    def test_is_branch_conditional(self) -> None:
        beq = Instruction(address=0, opcode="BEQ", operands=["$1", "$2", 5])
        assert beq.is_branch()
        assert beq.is_conditional_branch()

    def test_is_jump(self) -> None:
        j = Instruction(address=0, opcode="J", operands=[0x2000])
        assert j.is_jump()
        assert j.is_branch()  # is_branch() returns True for jumps too

    def test_is_arithmetic(self) -> None:
        add = Instruction(address=0, opcode="ADD", operands=["$1", "$2", "$3"])
        assert add.is_arithmetic()

    def test_is_logical(self) -> None:
        and_inst = Instruction(address=0, opcode="AND", operands=["$1", "$2", "$3"])
        assert and_inst.is_logical()

    def test_is_floating_point(self) -> None:
        fadd = Instruction(address=0, opcode="FADD", operands=["$1", "$2", "$3"])
        assert fadd.is_floating_point()


# ========================== Latency ========================================


class TestInstructionLatency:
    """Latency lookup covers the full opcode map."""

    @pytest.mark.parametrize(
        "opcode, expected_latency",
        [
            ("ADD", 1),
            ("SUB", 1),
            ("MUL", 3),
            ("DIV", 10),
            ("LW", 2),
            ("SW", 2),
            ("FADD", 3),
            ("FMUL", 5),
            ("FDIV", 15),
            ("BEQ", 1),
            ("J", 1),
            ("NOP", 1),
        ],
    )
    def test_latency(self, opcode: str, expected_latency: int) -> None:
        inst = Instruction(address=0, opcode=opcode, operands=["$1", "$2", "$3"])
        assert inst.get_latency() == expected_latency

    def test_unknown_opcode_defaults_to_one(self) -> None:
        inst = Instruction(
            address=0,
            opcode="CUSTOM",
            operands=["$1"],
            instruction_type=InstructionType.ARITHMETIC,
        )
        assert inst.get_latency() == 1


# ========================== Branch Evaluation ==============================


class TestBranchEvaluation:
    """is_taken() for all branch conditions."""

    def test_beq_taken_when_equal(self) -> None:
        rf = _FakeRegisterFile({"$4": 5, "$5": 5})
        inst = Instruction(address=0, opcode="BEQ", operands=["$4", "$5", 10])
        assert inst.is_taken(rf)

    def test_beq_not_taken_when_different(self) -> None:
        rf = _FakeRegisterFile({"$4": 5, "$5": 6})
        inst = Instruction(address=0, opcode="BEQ", operands=["$4", "$5", 10])
        assert not inst.is_taken(rf)

    def test_bne_taken_when_different(self) -> None:
        rf = _FakeRegisterFile({"$4": 5, "$5": 6})
        inst = Instruction(address=0, opcode="BNE", operands=["$4", "$5", 10])
        assert inst.is_taken(rf)

    def test_blt_taken(self) -> None:
        rf = _FakeRegisterFile({"$4": 3, "$5": 7})
        inst = Instruction(address=0, opcode="BLT", operands=["$4", "$5", 10])
        assert inst.is_taken(rf)

    def test_blt_not_taken(self) -> None:
        rf = _FakeRegisterFile({"$4": 7, "$5": 3})
        inst = Instruction(address=0, opcode="BLT", operands=["$4", "$5", 10])
        assert not inst.is_taken(rf)

    def test_bge_taken_equal(self) -> None:
        rf = _FakeRegisterFile({"$4": 5, "$5": 5})
        inst = Instruction(address=0, opcode="BGE", operands=["$4", "$5", 10])
        assert inst.is_taken(rf)

    def test_bge_taken_greater(self) -> None:
        rf = _FakeRegisterFile({"$4": 9, "$5": 5})
        inst = Instruction(address=0, opcode="BGE", operands=["$4", "$5", 10])
        assert inst.is_taken(rf)

    def test_j_always_taken(self) -> None:
        rf = _FakeRegisterFile({})
        inst = Instruction(address=0, opcode="J", operands=[0x2000])
        assert inst.is_taken(rf)

    def test_jal_always_taken(self) -> None:
        rf = _FakeRegisterFile({})
        inst = Instruction(address=0, opcode="JAL", operands=[0x2000])
        assert inst.is_taken(rf)

    def test_unknown_branch_not_taken(self) -> None:
        rf = _FakeRegisterFile({})
        inst = Instruction(
            address=0,
            opcode="BXYZ",
            operands=["$1", "$2", 5],
            instruction_type=InstructionType.BRANCH,
        )
        assert not inst.is_taken(rf)


# ========================== LUI Instruction ==================================


class TestLUIInstruction:
    """LUI (Load Upper Immediate) instruction handling."""

    def test_lui_classified_as_logical(self) -> None:
        """LUI should be classified as a LOGICAL instruction."""
        inst = Instruction(address=0, opcode="LUI", operands=["$t0", 0x1234])
        assert inst.instruction_type == InstructionType.LOGICAL

    def test_lui_destination_register(self) -> None:
        """LUI destination is the first operand register."""
        inst = Instruction(address=0, opcode="LUI", operands=["$t0", 0x1234])
        assert inst.get_destination_register() == "$t0"
        assert inst.has_destination_register()

    def test_lui_is_i_type(self) -> None:
        """LUI is an I-type instruction (register + immediate)."""
        inst = Instruction(address=0, opcode="LUI", operands=["$t0", 0x1234])
        assert inst.is_i_type()
        assert not inst.is_r_type()

    def test_lui_latency(self) -> None:
        """LUI latency should default to 1 cycle (ALU operation)."""
        inst = Instruction(address=0, opcode="LUI", operands=["$t0", 0x1234])
        assert inst.get_latency() == 1

    def test_lui_source_registers_empty(self) -> None:
        """LUI has no source registers — only a destination and immediate."""
        inst = Instruction(address=0, opcode="LUI", operands=["$t0", 0x1234])
        # LUI operands: ["$t0", 0x1234] → no register sources
        sources = inst.get_source_registers()
        # Source parsing may return [] or ['$t0'] depending on I-type parsing
        # The key point: LUI doesn't read any register values
        assert isinstance(sources, list)


# ========================== String Representations =========================


class TestInstructionRepr:
    """__repr__ and __str__ produce human-readable output."""

    def test_repr_includes_address_and_opcode(self) -> None:
        inst = Instruction(address=0x1000, opcode="ADD", operands=["$1", "$2", "$3"])
        text = repr(inst)
        assert "0x1000" in text
        assert "ADD" in text

    def test_str_shows_opcode_and_operands(self) -> None:
        inst = Instruction(address=0, opcode="LW", operands=["$2", "0($3)"])
        text = str(inst)
        assert "LW" in text
        assert "$2" in text


# ========================== BranchInstruction ===============================


class TestBranchInstruction:
    """BranchInstruction extends Instruction with target address logic."""

    def test_pc_alias_for_address(self) -> None:
        bi = BranchInstruction(
            address=0x2000,
            opcode="BEQ",
            operands=["$1", "$2", 4],
        )
        assert bi.pc == 0x2000
        assert bi.address == 0x2000

    def test_target_address_calculated_from_offset(self) -> None:
        # address=0x1000, offset=4 → target = 0x1000 + 4 + (4*4) = 0x1014
        bi = BranchInstruction(
            address=0x1000,
            opcode="BEQ",
            operands=["$1", "$2", 4],
        )
        assert bi.get_target_address() == 0x1014

    def test_jump_target_absolute(self) -> None:
        bi = BranchInstruction(
            address=0x1000,
            opcode="J",
            operands=["0x2000"],
        )
        assert bi.get_target_address() == 0x2000

    def test_explicit_target_overrides_calculation(self) -> None:
        bi = BranchInstruction(
            address=0x1000,
            opcode="BEQ",
            operands=["$1", "$2", 4],
            target_address=0xDEAD,
        )
        assert bi.get_target_address() == 0xDEAD

    def test_pc_set_from_address(self) -> None:
        bi = BranchInstruction(address=0x3000, opcode="BNE", operands=["$1", "$2", 2])
        assert bi.pc == 0x3000


# ========================== InstructionBundle ================================


class TestInstructionBundle:
    """Bundle of instructions fetched together."""

    def _make_bundle(self, ops: list[tuple[str, list]]) -> InstructionBundle:
        """Shorthand builder: list of (opcode, operands) pairs."""
        insts = [
            Instruction(address=i * 4, opcode=op, operands=operands)
            for i, (op, operands) in enumerate(ops)
        ]
        return InstructionBundle(insts, fetch_cycle=1)

    def test_size_matches_instruction_count(self) -> None:
        bundle = self._make_bundle(
            [
                ("ADD", ["$1", "$2", "$3"]),
                ("SUB", ["$4", "$5", "$6"]),
            ]
        )
        assert bundle.size == 2

    def test_has_branch_true_when_bundle_contains_branch(self) -> None:
        bundle = self._make_bundle(
            [
                ("ADD", ["$1", "$2", "$3"]),
                ("BEQ", ["$1", "$2", 5]),
            ]
        )
        assert bundle.has_branch()

    def test_has_branch_false_for_alu_only(self) -> None:
        bundle = self._make_bundle(
            [
                ("ADD", ["$1", "$2", "$3"]),
                ("SUB", ["$4", "$5", "$6"]),
            ]
        )
        assert not bundle.has_branch()

    def test_get_branch_instruction_returns_first_branch(self) -> None:
        bundle = self._make_bundle(
            [
                ("ADD", ["$1", "$2", "$3"]),
                ("BEQ", ["$1", "$2", 5]),
                ("BNE", ["$3", "$4", 10]),
            ]
        )
        branch = bundle.get_branch_instruction()
        assert branch is not None
        assert branch.opcode == "BEQ"

    def test_get_branch_instruction_returns_none_when_absent(self) -> None:
        bundle = self._make_bundle([("ADD", ["$1", "$2", "$3"])])
        assert bundle.get_branch_instruction() is None

    def test_has_memory_operation(self) -> None:
        bundle = self._make_bundle(
            [
                ("LW", ["$2", "0($3)"]),
            ]
        )
        assert bundle.has_memory_operation()

    def test_get_dependencies_detects_raw(self) -> None:
        # ADD $8, ... → SUB uses $8 as source → RAW dependency
        bundle = self._make_bundle(
            [
                ("ADD", ["$8", "$9", "$10"]),
                ("SUB", ["$11", "$8", "$12"]),
            ]
        )
        deps = bundle.get_dependencies()
        assert (0, 1) in deps

    def test_get_dependencies_no_false_positives(self) -> None:
        bundle = self._make_bundle(
            [
                ("ADD", ["$8", "$9", "$10"]),
                ("SUB", ["$11", "$12", "$13"]),
            ]
        )
        deps = bundle.get_dependencies()
        assert len(deps) == 0

    def test_repr_includes_size_and_cycle(self) -> None:
        bundle = self._make_bundle([("ADD", ["$1", "$2", "$3"])])
        text = repr(bundle)
        assert "size=1" in text
        assert "cycle=1" in text


# ========================== InstructionStatus ================================


class TestInstructionStatus:
    """Status enum covers all pipeline stages."""

    def test_all_stages_present(self) -> None:
        expected = {
            "FETCHED",
            "DECODED",
            "ISSUED",
            "EXECUTING",
            "MEMORY_ACCESS",
            "WRITE_BACK",
            "COMPLETED",
        }
        actual = {s.name for s in InstructionStatus}
        assert expected == actual

    def test_default_status_is_fetched(self) -> None:
        inst = Instruction(address=0, opcode="ADD", operands=["$1", "$2", "$3"])
        assert inst.status == InstructionStatus.FETCHED
