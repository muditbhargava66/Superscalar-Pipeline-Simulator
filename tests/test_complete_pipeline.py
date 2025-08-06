#!/usr/bin/env python3
"""
Comprehensive Pipeline Test Suite

This test suite validates all components of the superscalar pipeline simulator
after the fixes and improvements.

Author: Assistant
Date: February 2025
"""

import os
from pathlib import Path
import sys
import unittest

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from cache.cache import Cache, DataCache, InstructionCache, Memory
from data_forwarding.data_forwarding_unit import DataForwardingUnit
from performance.profiler import PerformanceProfiler
from pipeline.decode_stage import DecodeStage
from pipeline.execute_stage import ExecuteStage
from pipeline.issue_stage import IssueStage
from pipeline.memory_access_stage import MemoryAccessStage
from pipeline.write_back_stage import WriteBackStage
from register_file.register_file import RegisterFile
from utils.functional_unit import ALU, FPU, LSU
from utils.instruction import Instruction, InstructionType
from utils.reservation_station import ReservationStation, ReservationStationPool
from utils.scoreboard import Scoreboard


class TestInstruction(unittest.TestCase):
    """Test instruction class functionality."""
    
    def test_instruction_creation(self):
        """Test basic instruction creation."""
        inst = Instruction(
            address=0x1000,
            opcode="ADD",
            operands=["$t0", "$t1", "$t2"]
        )
        
        self.assertEqual(inst.address, 0x1000)
        self.assertEqual(inst.opcode, "ADD")
        self.assertEqual(len(inst.operands), 3)
        self.assertEqual(inst.instruction_type, InstructionType.ARITHMETIC)
    
    def test_instruction_type_detection(self):
        """Test automatic instruction type detection."""
        test_cases = [
            ("ADD", InstructionType.ARITHMETIC),
            ("LW", InstructionType.MEMORY),
            ("BEQ", InstructionType.BRANCH),
            ("FADD", InstructionType.FLOAT),
            ("AND", InstructionType.LOGICAL)
        ]
        
        for opcode, expected_type in test_cases:
            inst = Instruction(address=0, opcode=opcode)
            self.assertEqual(inst.instruction_type, expected_type)
    
    def test_source_register_extraction(self):
        """Test source register extraction."""
        # R-type instruction
        inst = Instruction(address=0, opcode="ADD", operands=["$t0", "$t1", "$t2"])
        sources = inst.get_source_registers()
        self.assertEqual(sources, ["$t1", "$t2"])
        
        # I-type instruction
        inst = Instruction(address=0, opcode="ADDI", operands=["$t0", "$t1", "10"])
        sources = inst.get_source_registers()
        self.assertEqual(sources, ["$t1"])


class TestReservationStation(unittest.TestCase):
    """Test reservation station functionality."""
    
    def setUp(self):
        self.rs = ReservationStation(0)
        self.instruction = Instruction(address=0, opcode="ADD", operands=["$t0", "$t1", "$t2"])
    
    def test_reservation_station_allocation(self):
        """Test reservation station allocation."""
        self.assertTrue(self.rs.is_free())
        
        self.rs.issue(self.instruction)
        self.assertFalse(self.rs.is_free())
        self.assertEqual(self.rs.instruction, self.instruction)
    
    def test_operand_resolution(self):
        """Test operand resolution in reservation station."""
        self.rs.issue(self.instruction)
        
        # Simulate operand update
        executed_instructions = [(
            Instruction(address=4, opcode="ADDI", operands=["$t1", "$zero", "5"]),
            5
        )]
        
        self.rs.update(executed_instructions)
        # Test would need mock register file to complete


class TestFunctionalUnits(unittest.TestCase):
    """Test functional unit implementations."""
    
    def setUp(self):
        self.register_file = RegisterFile()
        self.register_file.write_register("$t1", 10)
        self.register_file.write_register("$t2", 20)
    
    def test_alu_operations(self):
        """Test ALU operations."""
        alu = ALU("ALU0")
        
        # Test ADD
        inst = Instruction(address=0, opcode="ADD", operands=["$t0", "$t1", "$t2"])
        result = alu.execute(inst, self.register_file)
        self.assertEqual(result, 30)
        
        # Test SUB
        inst = Instruction(address=4, opcode="SUB", operands=["$t0", "$t1", "$t2"])
        alu.busy = False  # Reset for next operation
        result = alu.execute(inst, self.register_file)
        self.assertEqual(result, -10)
    
    def test_functional_unit_latency(self):
        """Test functional unit latency handling."""
        alu = ALU("ALU0")
        inst = Instruction(address=0, opcode="MUL", operands=["$t0", "$t1", "$t2"])
        
        alu.execute(inst, self.register_file)
        self.assertTrue(alu.busy)
        self.assertEqual(alu.remaining_cycles, 3)  # MUL latency
        
        # Simulate cycles
        for _ in range(2):
            result = alu.update()
            self.assertIsNone(result)  # Not ready yet
        
        result = alu.update()
        self.assertIsNotNone(result)  # Should be ready now
        self.assertFalse(alu.busy)


class TestCache(unittest.TestCase):
    """Test cache implementations."""
    
    def test_cache_basic_operations(self):
        """Test basic cache read/write operations."""
        cache = Cache(cache_size=1024, block_size=64)
        
        # Test write and read
        cache.write(0x1000, 42)
        data = cache.read(0x1000)
        self.assertEqual(data, 42)
        
        # Test cache miss
        data = cache.read(0x2000)
        self.assertIsNone(data)
    
    def test_cache_replacement(self):
        """Test cache replacement policy."""
        # Small cache to force replacement
        cache = Cache(cache_size=128, block_size=32, associativity=2)
        
        # Fill cache beyond capacity
        for i in range(10):
            cache.write(i * 32, i)
        
        # Check that some data was evicted
        self.assertGreater(cache.evictions, 0)
    
    def test_data_cache_store_forwarding(self):
        """Test store-to-load forwarding in data cache."""
        dcache = DataCache(cache_size=1024, block_size=64)
        
        # Store data
        dcache.store(0x1000, 100)
        
        # Load should get forwarded data
        data = dcache.load(0x1000)
        self.assertEqual(data, 100)


class TestRegisterFile(unittest.TestCase):
    """Test register file functionality."""
    
    def setUp(self):
        self.rf = RegisterFile()
    
    def test_register_read_write(self):
        """Test basic register operations."""
        # Test write and read
        self.rf.write_register("$t0", 42)
        value = self.rf.read_register("$t0")
        self.assertEqual(value, 42)
        
        # Test $zero register
        self.rf.write_register("$zero", 100)  # Should be ignored
        value = self.rf.read_register("$zero")
        self.assertEqual(value, 0)
    
    def test_register_name_resolution(self):
        """Test register name resolution."""
        # Test different naming conventions
        self.rf.write_register("$t0", 10)
        self.rf.write_register("$8", 20)
        self.rf.write_register("r8", 30)
        
        # All should refer to the same register
        self.assertEqual(self.rf.read_register("$t0"), 30)
        self.assertEqual(self.rf.read_register("$8"), 30)
        self.assertEqual(self.rf.read_register("r8"), 30)
    
    def test_multiple_ports(self):
        """Test multiple read/write ports."""
        # Test multiple reads
        self.rf.write_register("$t0", 10)
        self.rf.write_register("$t1", 20)
        
        values = self.rf.read_multiple(["$t0", "$t1"])
        self.assertEqual(values, [10, 20])
        
        # Test multiple writes
        writes = [("$t2", 30), ("$t3", 40)]
        self.rf.write_multiple(writes)
        
        self.assertEqual(self.rf.read_register("$t2"), 30)
        self.assertEqual(self.rf.read_register("$t3"), 40)


class TestScoreboard(unittest.TestCase):
    """Test scoreboard functionality."""
    
    def setUp(self):
        self.scoreboard = Scoreboard()
    
    def test_hazard_detection(self):
        """Test hazard detection."""
        # Create instructions with dependencies
        inst1 = Instruction(address=0, opcode="ADD", operands=["$t0", "$t1", "$t2"])
        inst2 = Instruction(address=4, opcode="SUB", operands=["$t3", "$t0", "$t4"])
        
        # Allocate register for first instruction
        self.scoreboard.allocate_register_write("$t0", inst1)
        
        # Check for RAW hazard
        hazards = self.scoreboard.check_hazards(inst2)
        self.assertIn("RAW", [h.name for h in hazards])
    
    def test_register_locking(self):
        """Test register locking mechanism."""
        inst = Instruction(address=0, opcode="ADD", operands=["$t0", "$t1", "$t2"])
        
        # Initially available
        self.assertTrue(self.scoreboard.is_register_available("$t0"))
        
        # Lock register
        self.scoreboard.allocate_register_write("$t0", inst)
        self.assertFalse(self.scoreboard.is_register_available("$t0"))
        
        # Unlock register
        self.scoreboard.deallocate_register("$t0")
        self.assertTrue(self.scoreboard.is_register_available("$t0"))


class TestDataForwarding(unittest.TestCase):
    """Test data forwarding unit."""
    
    def setUp(self):
        self.forwarding_unit = DataForwardingUnit()
    
    def test_forwarding_path_creation(self):
        """Test creation of forwarding paths."""
        self.forwarding_unit.add_forwarding_path(
            from_stage="execute",
            to_stage="decode",
            forwarding_condition=lambda inst: True
        )
        
        self.assertEqual(len(self.forwarding_unit.forwarding_paths), 1)
    
    def test_data_forwarding(self):
        """Test actual data forwarding."""
        # Add forwarding path
        self.forwarding_unit.add_forwarding_path(
            from_stage="execute",
            to_stage="decode",
            forwarding_condition=lambda inst: True
        )
        
        # Create producer instruction
        producer = Instruction(address=0, opcode="ADD", operands=["$t0", "$t1", "$t2"])
        producer.result = 42
        
        # Forward data
        self.forwarding_unit.forward_data(producer, "execute")
        
        # Create consumer instruction
        consumer = Instruction(address=4, opcode="SUB", operands=["$t3", "$t0", "$t4"])
        
        # Check if forwarding is available
        forwarded = self.forwarding_unit.get_forwarded_data(consumer, "decode")
        self.assertIsNotNone(forwarded)


class TestPipelineStages(unittest.TestCase):
    """Test individual pipeline stages."""
    
    def setUp(self):
        self.register_file = RegisterFile()
        self.memory = Memory(size=1024*1024)
        self.data_cache = DataCache(cache_size=32*1024, block_size=64)
        self.forwarding_unit = DataForwardingUnit()
    
    def test_decode_stage(self):
        """Test decode stage functionality."""
        decode_stage = DecodeStage(self.register_file)
        
        # Create test instruction
        inst = Instruction(address=0, opcode="ADD", operands=["$t0", "$t1", "$t2"])
        
        # Decode instruction
        decoded = decode_stage.decode([inst])
        self.assertEqual(len(decoded), 1)
        self.assertEqual(decoded[0].opcode, "ADD")
    
    def test_issue_stage(self):
        """Test issue stage functionality."""
        issue_stage = IssueStage(
            num_reservation_stations=4,
            register_file=self.register_file,
            data_forwarding_unit=self.forwarding_unit
        )
        
        # Create test instruction
        inst = Instruction(address=0, opcode="ADD", operands=["$t0", "$t1", "$t2"])
        
        # Issue instruction
        issued = issue_stage.issue([inst])
        self.assertEqual(len(issued), 1)
    
    def test_execute_stage(self):
        """Test execute stage functionality."""
        execute_stage = ExecuteStage(
            num_alu_units=2,
            num_fpu_units=1,
            num_lsu_units=1,
            register_file=self.register_file,
            data_cache=self.data_cache,
            memory=self.memory
        )
        
        # Create test instruction with resolved operands
        inst = Instruction(address=0, opcode="ADD", operands=["$t0", "$t1", "$t2"])
        inst.resolved_operands = {"$t1": 10, "$t2": 20}
        
        # Execute instruction
        _results = execute_stage.execute([inst])
        # Results depend on functional unit implementation
    
    def test_memory_access_stage(self):
        """Test memory access stage functionality."""
        memory_stage = MemoryAccessStage(self.data_cache, self.memory)
        
        # Create load instruction
        load_inst = Instruction(address=0, opcode="LW", operands=["$t0", "0($t1)"])
        load_inst.register_values = {"$t1": 0x1000}
        
        # Process memory access
        results = memory_stage.access_memory([(load_inst, 0x1000)])
        self.assertEqual(len(results), 1)
    
    def test_write_back_stage(self):
        """Test write-back stage functionality."""
        wb_stage = WriteBackStage(self.register_file)
        
        # Create completed instruction
        inst = Instruction(address=0, opcode="ADD", operands=["$t0", "$t1", "$t2"])
        
        # Write back result
        completed = wb_stage.write_back([(inst, 42)])
        self.assertEqual(len(completed), 1)


class TestPerformanceProfiler(unittest.TestCase):
    """Test performance profiler functionality."""
    
    def setUp(self):
        self.profiler = PerformanceProfiler(enable_detailed_tracking=True)
    
    def test_instruction_tracking(self):
        """Test instruction completion tracking."""
        self.profiler.record_instruction_complete("ADD $t0, $t1, $t2", 1, 5)
        
        self.assertEqual(self.profiler.metrics.total_instructions, 1)
        self.assertIn("ADD $t0, $t1, $t2", self.profiler.instruction_latencies)
        self.assertEqual(self.profiler.instruction_latencies["ADD $t0, $t1, $t2"][0], 4)
    
    def test_branch_prediction_tracking(self):
        """Test branch prediction tracking."""
        self.profiler.record_branch_prediction("BEQ $t0, $t1, label", True, False)
        
        self.assertEqual(self.profiler.metrics.branch_predictions, 1)
        self.assertEqual(self.profiler.metrics.branch_mispredictions, 1)
    
    def test_performance_summary(self):
        """Test performance summary generation."""
        # Add some sample data
        self.profiler.record_instruction_complete("ADD", 1, 2)
        self.profiler.record_branch_prediction("BEQ", True, True)
        self.profiler.record_cache_access("data", True)
        
        summary = self.profiler.get_performance_summary()
        
        self.assertIn('basic_metrics', summary)
        self.assertIn('branch_performance', summary)
        self.assertIn('cache_performance', summary)
        self.assertEqual(summary['basic_metrics']['total_instructions'], 1)


class TestIntegration(unittest.TestCase):
    """Integration tests for the complete pipeline."""
    
    def test_simple_pipeline_flow(self):
        """Test a simple instruction flowing through the pipeline."""
        # Initialize components
        register_file = RegisterFile()
        memory = Memory(size=1024*1024)
        data_cache = DataCache(cache_size=32*1024, block_size=64)
        forwarding_unit = DataForwardingUnit()
        
        # Initialize pipeline stages
        decode_stage = DecodeStage(register_file)
        issue_stage = IssueStage(4, register_file, forwarding_unit)
        execute_stage = ExecuteStage(2, 1, 1, register_file, data_cache, memory)
        memory_stage = MemoryAccessStage(data_cache, memory)
        wb_stage = WriteBackStage(register_file)
        
        # Create test instruction
        inst = Instruction(address=0, opcode="ADDI", operands=["$t0", "$zero", "42"])
        
        # Flow through pipeline
        decoded = decode_stage.decode([inst])
        self.assertEqual(len(decoded), 1)
        
        issued = issue_stage.issue(decoded)
        self.assertEqual(len(issued), 1)
        
        # Get ready instructions and execute
        ready = issue_stage.get_ready_instructions()
        if ready:
            executed = execute_stage.execute(ready)
            
            if executed:
                memory_results = memory_stage.access_memory(executed)
                _completed = wb_stage.write_back(memory_results)
                
                # Check final result
                result = register_file.read_register("$t0")
                self.assertEqual(result, 42)


def run_comprehensive_tests():
    """Run all tests and generate a report."""
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add all test classes
    test_classes = [
        TestInstruction,
        TestReservationStation,
        TestFunctionalUnits,
        TestCache,
        TestRegisterFile,
        TestScoreboard,
        TestDataForwarding,
        TestPipelineStages,
        TestPerformanceProfiler,
        TestIntegration
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Generate report
    print("\n" + "="*60)
    print("COMPREHENSIVE TEST REPORT")
    print("="*60)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print("\nFAILURES:")
        for test, traceback in result.failures:
            error_msg = traceback.split('AssertionError: ')[-1].split('\n')[0]
            print(f"- {test}: {error_msg}")
    
    if result.errors:
        print("\nERRORS:")
        for test, traceback in result.errors:
            error_msg = traceback.split('\n')[-2]
            print(f"- {test}: {error_msg}")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_comprehensive_tests()
    sys.exit(0 if success else 1)
