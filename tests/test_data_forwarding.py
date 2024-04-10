import unittest
from src.data_forwarding import DataForwardingUnit
from src.utils import Instruction

class TestDataForwarding(unittest.TestCase):
    def setUp(self):
        # Set up the necessary components for testing
        self.forwarding_unit = DataForwardingUnit()
        
        # Define forwarding paths
        self.forwarding_unit.add_forwarding_path(from_stage='execute', to_stage='decode', forwarding_condition=lambda instr: True)
        self.forwarding_unit.add_forwarding_path(from_stage='memory', to_stage='execute', forwarding_condition=lambda instr: instr.is_load())
    
    def test_data_forwarding(self):
        # Test case for data forwarding
        instruction1 = Instruction(opcode='ADD', operands=[1, 2], destination=3)
        instruction2 = Instruction(opcode='SUB', operands=[3, 4], destination=5)
        instruction3 = Instruction(opcode='MUL', operands=[5, 6], destination=7)
        
        # Set up the initial state of the pipeline
        self.forwarding_unit.get_data_from_stage = lambda instr, stage: 10 if stage == 'execute' else None
        
        # Perform data forwarding
        self.forwarding_unit.forward_data(instruction1, stage='decode')
        self.forwarding_unit.forward_data(instruction2, stage='execute')
        self.forwarding_unit.forward_data(instruction3, stage='memory')
        
        # Assert the correctness of forwarded data
        self.assertEqual(instruction1.operands, [1, 2])  # No forwarding in decode stage
        self.assertEqual(instruction2.operands, [10, 4])  # Forwarding from execute to decode
        self.assertEqual(instruction3.operands, [5, 6])  # No forwarding in memory stage
    
    def test_load_forwarding(self):
        # Test case for load instruction forwarding
        load_instruction = Instruction(opcode='LOAD', operands=[1], destination=2)
        dependent_instruction = Instruction(opcode='ADD', operands=[2, 3], destination=4)
        
        # Set up the initial state of the pipeline
        self.forwarding_unit.get_data_from_stage = lambda instr, stage: 20 if stage == 'memory' else None
        
        # Perform data forwarding
        self.forwarding_unit.forward_data(load_instruction, stage='memory')
        self.forwarding_unit.forward_data(dependent_instruction, stage='execute')
        
        # Assert the correctness of forwarded data
        self.assertEqual(load_instruction.operands, [1])  # No forwarding for load instruction
        self.assertEqual(dependent_instruction.operands, [20, 3])  # Forwarding from memory to execute

if __name__ == '__main__':
    unittest.main()