"""
Unit tests for data forwarding functionality.

This module tests the data forwarding unit and its integration
with the pipeline stages.

Author: Mudit Bhargava
Date: August2025
Python Version: 3.10+
"""

from pathlib import Path
import sys
import unittest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data_forwarding import DataForwardingUnit
from src.register_file import RegisterFile
from src.utils import Instruction


class TestDataForwarding(unittest.TestCase):
    """Test suite for data forwarding unit."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.forwarding_unit = DataForwardingUnit()
        self.register_file = RegisterFile(32)
        
        # Set up forwarding paths
        self.forwarding_unit.add_forwarding_path(
            from_stage='execute',
            to_stage='decode',
            forwarding_condition=lambda inst: True,
            priority=2
        )
        
        self.forwarding_unit.add_forwarding_path(
            from_stage='memory',
            to_stage='execute',
            forwarding_condition=lambda inst: inst.is_memory_operation() if hasattr(inst, 'is_memory_operation') else False,
            priority=1
        )
        
        self.forwarding_unit.add_forwarding_path(
            from_stage='writeback',
            to_stage='decode',
            forwarding_condition=lambda inst: inst.has_destination_register() if hasattr(inst, 'has_destination_register') else False,
            priority=0
        )
    
    def test_basic_forwarding(self):
        """Test basic data forwarding from execute to decode."""
        # Create producer instruction
        producer = Instruction(
            address=0x100,
            opcode="ADD",
            operands=["$t2", "$t0", "$t1"],
            destination="$t2"
        )
        producer.result = 42
        
        # Make data available for forwarding
        self.forwarding_unit.forward_data(producer, 'execute')
        
        # Create consumer instruction
        consumer = Instruction(
            address=0x104,
            opcode="SUB",
            operands=["$t3", "$t2", "$t4"],
            destination="$t3"
        )
        
        # Check if forwarding is available
        forwarded = self.forwarding_unit.get_forwarded_data(consumer, 'decode')
        
        self.assertIsNotNone(forwarded)
        self.assertIn("$t2", forwarded)
        self.assertEqual(forwarded["$t2"], 42)
    
    def test_no_forwarding_available(self):
        """Test when no forwarding is available."""
        # Create instruction needing data
        consumer = Instruction(
            address=0x100,
            opcode="ADD",
            operands=["$t0", "$s0", "$s1"],
            destination="$t0"
        )
        
        # No producer has made data available
        forwarded = self.forwarding_unit.get_forwarded_data(consumer, 'decode')
        
        self.assertIsNone(forwarded)
    
    def test_memory_forwarding(self):
        """Test forwarding from memory stage."""
        # Create load instruction
        load_inst = Instruction(
            address=0x100,
            opcode="LW",
            operands=["$t0", "0($sp)"],
            destination="$t0"
        )
        load_inst.result = 100
        
        # Forward from memory stage
        self.forwarding_unit.forward_data(load_inst, 'memory')
        
        # Create instruction using loaded value
        use_inst = Instruction(
            address=0x104,
            opcode="ADD",
            operands=["$t1", "$t0", "$t2"],
            destination="$t1"
        )
        
        # Memory forwarding only works for memory operations
        # So this should not get forwarded (based on our condition)
        forwarded = self.forwarding_unit.get_forwarded_data(use_inst, 'execute')
        self.assertIsNone(forwarded)
    
    def test_multiple_forwarding_sources(self):
        """Test handling multiple potential forwarding sources."""
        # First producer (older)
        producer1 = Instruction(
            address=0x100,
            opcode="ADD",
            operands=["$t0", "$t1", "$t2"],
            destination="$t0"
        )
        producer1.result = 10
        
        # Second producer (newer)
        producer2 = Instruction(
            address=0x104,
            opcode="SUB",
            operands=["$t0", "$t3", "$t4"],
            destination="$t0"
        )
        producer2.result = 20
        
        # Forward from different stages
        self.forwarding_unit.forward_data(producer1, 'writeback')
        self.forwarding_unit.forward_data(producer2, 'execute')
        
        # Consumer should get value from execute (higher priority)
        consumer = Instruction(
            address=0x108,
            opcode="MUL",
            operands=["$t5", "$t0", "$t6"],
            destination="$t5"
        )
        
        forwarded = self.forwarding_unit.get_forwarded_data(consumer, 'decode')
        
        self.assertIsNotNone(forwarded)
        self.assertEqual(forwarded["$t0"], 20)  # Should get newer value
    
    def test_apply_forwarding(self):
        """Test applying forwarded values to instruction."""
        # Set up producer
        producer = Instruction(
            address=0x100,
            opcode="ADD",
            operands=["$t0", "$t1", "$t2"],
            destination="$t0"
        )
        producer.result = 50
        
        self.forwarding_unit.forward_data(producer, 'execute')
        
        # Set up consumer
        consumer = Instruction(
            address=0x104,
            opcode="ADD",
            operands=["$t3", "$t0", "$t4"],
            destination="$t3"
        )
        consumer.register_values = {"$t0": 0, "$t4": 10}  # Initial values
        
        # Apply forwarding
        applied = self.forwarding_unit.apply_forwarding(consumer, 'decode')
        
        self.assertTrue(applied)
        self.assertEqual(consumer.register_values["$t0"], 50)
        self.assertEqual(consumer.forwarded_values["$t0"], 50)
    
    def test_dependency_check(self):
        """Test dependency checking between instructions."""
        # Producer
        producer = Instruction(
            address=0x100,
            opcode="ADD",
            operands=["$t0", "$t1", "$t2"],
            destination="$t0"
        )
        
        # Dependent consumer
        consumer1 = Instruction(
            address=0x104,
            opcode="SUB",
            operands=["$t3", "$t0", "$t4"],
            destination="$t3"
        )
        
        # Independent instruction
        consumer2 = Instruction(
            address=0x108,
            opcode="MUL",
            operands=["$t5", "$t6", "$t7"],
            destination="$t5"
        )
        
        # Check dependencies
        self.assertTrue(self.forwarding_unit.check_dependency(consumer1, producer))
        self.assertFalse(self.forwarding_unit.check_dependency(consumer2, producer))
    
    def test_forwarding_statistics(self):
        """Test forwarding unit statistics tracking."""
        # Generate some forwarding activity
        for i in range(10):
            producer = Instruction(
                address=0x100 + i*4,
                opcode="ADD",
                operands=[f"$t{i}", "$t0", "$t1"],
                destination=f"$t{i}"
            )
            producer.result = i * 10
            self.forwarding_unit.forward_data(producer, 'execute')
        
        # Create hits and misses
        for i in range(5):
            consumer = Instruction(
                address=0x200 + i*4,
                opcode="SUB",
                operands=["$s0", f"$t{i}", "$s1"],
                destination="$s0"
            )
            self.forwarding_unit.get_forwarded_data(consumer, 'decode')
        
        # Check statistics
        stats = self.forwarding_unit.get_statistics()
        
        self.assertEqual(stats['forwards_created'], 10)
        self.assertEqual(stats['forward_hits'], 5)
        self.assertGreater(stats['forward_misses'], 0)
        self.assertEqual(stats['active_paths'], 3)
    
    def test_cycle_data_clearing(self):
        """Test clearing forwarding data between cycles."""
        # Add forwarding data
        inst = Instruction(
            address=0x100,
            opcode="ADD",
            operands=["$t0", "$t1", "$t2"],
            destination="$t0"
        )
        inst.result = 100
        
        self.forwarding_unit.forward_data(inst, 'execute')
        
        # Verify data is available
        self.assertIn('execute', self.forwarding_unit.current_forwards)
        
        # Clear cycle data
        self.forwarding_unit.clear_cycle_data()
        
        # Verify data is cleared
        self.assertEqual(len(self.forwarding_unit.current_forwards), 0)
    
    def test_forwarding_with_branches(self):
        """Test forwarding with branch instructions."""
        # Branch instruction doesn't produce forwardable data
        branch = Instruction(
            address=0x100,
            opcode="BEQ",
            operands=["$t0", "$t1", "label"],
            destination=None
        )
        
        self.forwarding_unit.forward_data(branch, 'execute')
        
        # Consumer shouldn't get any forwarded data
        consumer = Instruction(
            address=0x104,
            opcode="ADD",
            operands=["$t2", "$t0", "$t1"],
            destination="$t2"
        )
        
        forwarded = self.forwarding_unit.get_forwarded_data(consumer, 'decode')
        self.assertIsNone(forwarded)


class TestAdvancedDataForwarding(unittest.TestCase):
    """Test suite for advanced data forwarding features."""
    
    def setUp(self):
        """Set up test fixtures."""
        from src.data_forwarding.data_forwarding_unit import AdvancedDataForwardingUnit
        self.forwarding_unit = AdvancedDataForwardingUnit()
        
        # Set up paths
        self.forwarding_unit.add_forwarding_path(
            'execute', 'decode', lambda i: True, priority=2
        )
    
    def test_forwarding_conflict_resolution(self):
        """Test resolution of forwarding conflicts."""
        from src.data_forwarding.data_forwarding_unit import ForwardedData
        
        # Create conflicting sources
        inst1 = Instruction(0x100, "ADD", ["$t0", "$t1", "$t2"], "$t0")
        inst2 = Instruction(0x104, "SUB", ["$t0", "$t3", "$t4"], "$t0")
        
        sources = [
            ForwardedData(inst1, "$t0", 10, "execute", 100),
            ForwardedData(inst2, "$t0", 20, "memory", 101)
        ]
        
        # Resolve conflict
        selected = self.forwarding_unit.resolve_forwarding_conflict("$t0", sources)
        
        self.assertIsNotNone(selected)
        self.assertEqual(selected.cycle, 101)  # Most recent
        self.assertEqual(selected.value, 20)
    
    def test_forwarding_latency(self):
        """Test forwarding latency calculation."""
        # Same stage
        latency = self.forwarding_unit.get_forwarding_latency('execute', 'execute')
        self.assertEqual(latency, 0)
        
        # Forward path
        latency = self.forwarding_unit.get_forwarding_latency('execute', 'decode')
        self.assertEqual(latency, 0)  # Can forward in same cycle
        
        # Invalid path
        latency = self.forwarding_unit.get_forwarding_latency('invalid', 'decode')
        self.assertEqual(latency, 1)  # Default


if __name__ == '__main__':
    unittest.main()
