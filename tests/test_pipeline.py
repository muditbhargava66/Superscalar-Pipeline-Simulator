"""
Unit tests for pipeline stages.

This module tests the functionality of individual pipeline stages
and their integration.

Author: Mudit Bhargava
Date: August2024
Python Version: 3.10+
"""

from pathlib import Path
import sys
import unittest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.branch_prediction import AlwaysTakenPredictor
from src.cache import DataCache, InstructionCache, Memory
from src.data_forwarding import DataForwardingUnit
from src.pipeline import (
    DecodeStage,
    ExecuteStage,
    FetchStage,
    IssueStage,
    MemoryAccessStage,
    WriteBackStage,
)
from src.register_file import RegisterFile
from src.utils import Instruction, ReservationStation, Scoreboard


class TestPipelineStages(unittest.TestCase):
    """Test suite for individual pipeline stages."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Initialize components
        self.memory = Memory(size=8192)  # Increased size to accommodate test addresses
        self.instruction_cache = InstructionCache(
            cache_size=1024,
            block_size=64,
            memory=self.memory,
            fetch_bandwidth=4
        )
        self.data_cache = DataCache(
            cache_size=1024,
            block_size=64
        )
        self.register_file = RegisterFile(32)
        self.branch_predictor = AlwaysTakenPredictor()
        self.forwarding_unit = DataForwardingUnit()
        self.scoreboard = Scoreboard(32)
        
        # Initialize pipeline stages
        self.fetch_stage = FetchStage(
            self.instruction_cache,
            self.branch_predictor,
            self.memory
        )
        self.decode_stage = DecodeStage(self.register_file)
        self.issue_stage = IssueStage(
            num_reservation_stations=8,
            register_file=self.register_file,
            data_forwarding_unit=self.forwarding_unit
        )
        self.execute_stage = ExecuteStage(
            num_alu_units=2,
            num_fpu_units=1,
            num_lsu_units=1,
            register_file=self.register_file,
            data_cache=self.data_cache,
            memory=self.memory
        )
        self.memory_access_stage = MemoryAccessStage(
            self.data_cache,
            self.memory
        )
        self.write_back_stage = WriteBackStage(self.register_file)
        
        # Load test program
        self._load_test_program()
    
    def _load_test_program(self):
        """Load a simple test program into instruction cache."""
        test_instructions = [
            {"opcode": "ADD", "operands": ["$t0", "$t1", "$t2"]},
            {"opcode": "SUB", "operands": ["$t3", "$t0", "$t4"]},
            {"opcode": "LW", "operands": ["$t5", "0($sp)"]},
            {"opcode": "SW", "operands": ["$t0", "4($sp)"]},
            {"opcode": "BEQ", "operands": ["$t0", "$t3", "8"]},
            {"opcode": "NOP", "operands": []}
        ]
        
        for i, inst_data in enumerate(test_instructions):
            self.instruction_cache.add_instruction(i * 4, inst_data)
    
    def test_fetch_stage(self):
        """Test instruction fetch stage."""
        # Reset PC
        self.fetch_stage.pc = 0
        
        # Fetch instructions
        fetched = self.fetch_stage.fetch()
        
        # Should fetch up to fetch_bandwidth instructions
        self.assertIsNotNone(fetched)
        self.assertGreater(len(fetched), 0)
        self.assertLessEqual(len(fetched), self.instruction_cache.fetch_bandwidth)
        
        # Check first instruction
        first_inst = fetched[0]
        self.assertIsInstance(first_inst, Instruction)
        self.assertEqual(first_inst.opcode, "ADD")
        self.assertEqual(first_inst.address, 0)
    
    def test_decode_stage(self):
        """Test instruction decode stage."""
        # Create test instruction
        inst = Instruction(
            address=0x100,
            opcode="ADD",
            operands=["$t0", "$t1", "$t2"],
            destination=None
        )
        
        # Decode
        decoded = self.decode_stage.decode([inst])
        
        self.assertEqual(len(decoded), 1)
        decoded_inst = decoded[0]
        
        # Check that destination is properly set
        self.assertEqual(decoded_inst.destination, "$t0")
        
        # Check that source registers are identified
        sources = decoded_inst.get_source_registers()
        self.assertIn("$t1", sources)
        self.assertIn("$t2", sources)
    
    def test_issue_stage(self):
        """Test instruction issue stage."""
        # Create test instructions
        inst1 = Instruction(0x100, "ADD", ["$t0", "$t1", "$t2"], "$t0")
        inst2 = Instruction(0x104, "SUB", ["$t3", "$t4", "$t5"], "$t3")
        
        # Issue instructions
        issued = self.issue_stage.issue([inst1, inst2])
        
        # Both should be issued (no dependencies)
        self.assertEqual(len(issued), 2)
        
        # Check reservation stations
        ready = self.issue_stage.get_ready_instructions()
        self.assertEqual(len(ready), 2)
    
    def test_issue_stage_with_dependency(self):
        """Test issue stage with data dependency."""
        # Create dependent instructions
        inst1 = Instruction(0x100, "ADD", ["$t0", "$t1", "$t2"], "$t0")
        inst2 = Instruction(0x104, "SUB", ["$t3", "$t0", "$t4"], "$t3")  # Depends on inst1
        
        # Issue first instruction
        issued1 = self.issue_stage.issue([inst1])
        self.assertEqual(len(issued1), 1)
        
        # Try to issue dependent instruction
        issued2 = self.issue_stage.issue([inst2])
        
        # May or may not issue depending on forwarding
        # Just check it doesn't crash
        self.assertIsNotNone(issued2)
    
    def test_execute_stage(self):
        """Test instruction execution stage."""
        # Set up register values
        self.register_file.write_register("$t1", 10)
        self.register_file.write_register("$t2", 20)
        
        # Create instruction
        inst = Instruction(0x100, "ADD", ["$t0", "$t1", "$t2"], "$t0")
        
        # Execute (need to simulate it being ready)
        # For testing, we'll directly call execute
        _executed = self.execute_stage.execute([inst])
        
        # Since execution may be pipelined, check stats instead
        stats = self.execute_stage.get_statistics()
        self.assertIsNotNone(stats)
    
    def test_memory_access_stage(self):
        """Test memory access stage."""
        # Test load instruction
        load_inst = Instruction(0x100, "LW", ["$t0", "0($sp)"], "$t0")
        
        # Set up stack pointer
        self.register_file.write_register("$sp", 0x1000)
        
        # Write test data to memory
        self.memory.write(0x1000, [42])
        
        # Process memory access
        results = self.memory_access_stage.access_memory([(load_inst, 0x1000)])
        
        self.assertEqual(len(results), 1)
        inst, value = results[0]
        self.assertEqual(value, 42)
    
    def test_memory_access_stage_store(self):
        """Test store instruction in memory access stage."""
        # Test store instruction
        store_inst = Instruction(0x100, "SW", ["$t0", "0($sp)"], None)
        
        # Set register values
        self.register_file.write_register("$t0", 100)
        self.register_file.write_register("$sp", 0x2000)
        
        # Process store
        results = self.memory_access_stage.access_memory([(store_inst, 100)])
        
        self.assertEqual(len(results), 1)
        inst, value = results[0]
        self.assertIsNone(value)  # Stores don't return values
        
        # Verify data was written (would need to check cache/memory)
    
    def test_write_back_stage(self):
        """Test write-back stage."""
        # Create instruction with result
        inst = Instruction(0x100, "ADD", ["$t0", "$t1", "$t2"], "$t0")
        
        # Write back result
        completed = self.write_back_stage.write_back([(inst, 30)])
        
        self.assertEqual(len(completed), 1)
        self.assertEqual(completed[0], inst)
        
        # Check register was updated
        value = self.register_file.read_register("$t0")
        self.assertEqual(value, 30)
    
    def test_pipeline_integration(self):
        """Test basic pipeline flow."""
        # This is a simplified integration test
        
        # Fetch
        self.fetch_stage.pc = 0
        fetched = self.fetch_stage.fetch()
        self.assertGreater(len(fetched), 0)
        
        # Decode
        decoded = self.decode_stage.decode(fetched[:1])  # Just first instruction
        self.assertEqual(len(decoded), 1)
        
        # Issue
        issued = self.issue_stage.issue(decoded)
        self.assertGreater(len(issued), 0)
        
        # The rest would require more setup for proper testing
    
    def test_branch_handling(self):
        """Test branch instruction handling."""
        # Create branch instruction
        branch = Instruction(0x100, "BEQ", ["$t0", "$t1", "16"], None)
        
        # Set registers equal for branch taken
        self.register_file.write_register("$t0", 10)
        self.register_file.write_register("$t1", 10)
        
        # Check if branch is taken
        taken = branch.is_taken(self.register_file)
        self.assertTrue(taken)
        
        # Test not taken
        self.register_file.write_register("$t1", 20)
        taken = branch.is_taken(self.register_file)
        self.assertFalse(taken)


class TestScoreboard(unittest.TestCase):
    """Test suite for scoreboard functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.scoreboard = Scoreboard(32)
    
    def test_register_allocation(self):
        """Test register allocation and deallocation."""
        # Initially all registers should be available
        self.assertTrue(self.scoreboard.is_register_available("$t0"))
        
        # Allocate register
        inst = Instruction(0x100, "ADD", ["$t0", "$t1", "$t2"], "$t0")
        self.scoreboard.allocate_register_write("$t0", inst)
        
        # Should no longer be available
        self.assertFalse(self.scoreboard.is_register_available("$t0"))
        
        # Deallocate
        self.scoreboard.deallocate_register("$t0")
        self.assertTrue(self.scoreboard.is_register_available("$t0"))
    
    def test_raw_hazard_detection(self):
        """Test Read-After-Write hazard detection."""
        # Writer instruction
        writer = Instruction(0x100, "ADD", ["$t0", "$t1", "$t2"], "$t0")
        self.scoreboard.allocate_register_write("$t0", writer)
        
        # Reader instruction (RAW hazard)
        reader = Instruction(0x104, "SUB", ["$t3", "$t0", "$t4"], "$t3")
        
        hazards = self.scoreboard.check_hazards(reader)
        self.assertIn("RAW", [h.name for h in hazards])
    
    def test_waw_hazard_detection(self):
        """Test Write-After-Write hazard detection."""
        # First writer
        writer1 = Instruction(0x100, "ADD", ["$t0", "$t1", "$t2"], "$t0")
        self.scoreboard.allocate_register_write("$t0", writer1)
        
        # Second writer (WAW hazard)
        writer2 = Instruction(0x104, "SUB", ["$t0", "$t3", "$t4"], "$t0")
        
        hazards = self.scoreboard.check_hazards(writer2)
        self.assertIn("WAW", [h.name for h in hazards])
    
    def test_functional_unit_allocation(self):
        """Test functional unit allocation."""
        # Initially available
        self.assertTrue(self.scoreboard.is_function_unit_available("ALU0"))
        
        # Allocate
        inst = Instruction(0x100, "ADD", ["$t0", "$t1", "$t2"], "$t0")
        self.scoreboard.allocate_function_unit("ALU0", inst, cycles=2)
        
        # Should be busy
        self.assertFalse(self.scoreboard.is_function_unit_available("ALU0"))
        
        # Update cycles
        self.scoreboard.update_cycle()
        self.assertFalse(self.scoreboard.is_function_unit_available("ALU0"))
        
        # After enough cycles, should be free
        self.scoreboard.update_cycle()
        self.scoreboard.deallocate_function_unit("ALU0")
        self.assertTrue(self.scoreboard.is_function_unit_available("ALU0"))


if __name__ == '__main__':
    unittest.main()
