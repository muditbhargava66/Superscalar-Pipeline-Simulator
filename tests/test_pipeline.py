import unittest
from src.pipeline import FetchStage, DecodeStage, IssueStage, ExecuteStage, MemoryAccessStage, WriteBackStage
from src.utils import Instruction

class TestPipeline(unittest.TestCase):
    def setUp(self):
        # Set up the necessary components for testing
        self.instruction_cache = InstructionCache()
        self.branch_predictor = BranchPredictor()
        self.register_file = RegisterFile()
        self.data_cache = DataCache()
        
        # Initialize pipeline stages
        self.fetch_stage = FetchStage(self.instruction_cache, self.branch_predictor)
        self.decode_stage = DecodeStage(self.register_file)
        self.issue_stage = IssueStage(num_reservation_stations=4)
        self.execute_stage = ExecuteStage(num_functional_units=2)
        self.memory_access_stage = MemoryAccessStage(self.data_cache)
        self.write_back_stage = WriteBackStage(self.register_file)
    
    def test_fetch_stage(self):
        # Test case for the fetch stage
        # Add instructions to the instruction cache
        self.instruction_cache.add_instruction(0, 'ADD')
        self.instruction_cache.add_instruction(4, 'SUB')
        self.instruction_cache.add_instruction(8, 'MUL')
        
        # Fetch instructions
        fetched_instructions = self.fetch_stage.fetch()
        
        # Assert the correctness of fetched instructions
        self.assertEqual(len(fetched_instructions), 3)
        self.assertEqual(fetched_instructions[0].opcode, 'ADD')
        self.assertEqual(fetched_instructions[1].opcode, 'SUB')
        self.assertEqual(fetched_instructions[2].opcode, 'MUL')
    
    def test_decode_stage(self):
        # Test case for the decode stage
        # Create sample instructions
        instruction1 = Instruction(opcode='ADD', operands=[1, 2], destination=3)
        instruction2 = Instruction(opcode='SUB', operands=[4, 5], destination=6)
        
        # Decode instructions
        decoded_instructions = self.decode_stage.decode([instruction1, instruction2])
        
        # Assert the correctness of decoded instructions
        self.assertEqual(len(decoded_instructions), 2)
        self.assertEqual(decoded_instructions[0].opcode, 'ADD')
        self.assertEqual(decoded_instructions[0].operands, [1, 2])
        self.assertEqual(decoded_instructions[0].destination, 3)
        self.assertEqual(decoded_instructions[1].opcode, 'SUB')
        self.assertEqual(decoded_instructions[1].operands, [4, 5])
        self.assertEqual(decoded_instructions[1].destination, 6)
    
    def test_issue_stage(self):
        # Test case for the issue stage
        # Create sample instructions
        instruction1 = Instruction(opcode='ADD', operands=[1, 2], destination=3)
        instruction2 = Instruction(opcode='SUB', operands=[4, 5], destination=6)
        
        # Issue instructions
        issued_instructions = self.issue_stage.issue([instruction1, instruction2])
        
        # Assert the correctness of issued instructions
        self.assertEqual(len(issued_instructions), 2)
        self.assertIn(instruction1, issued_instructions)
        self.assertIn(instruction2, issued_instructions)
    
    def test_execute_stage(self):
        # Test case for the execute stage
        # Create sample instructions
        instruction1 = Instruction(opcode='ADD', operands=[1, 2], destination=3)
        instruction2 = Instruction(opcode='SUB', operands=[4, 5], destination=6)
        
        # Execute instructions
        executed_instructions = self.execute_stage.execute([instruction1, instruction2])
        
        # Assert the correctness of executed instructions
        self.assertEqual(len(executed_instructions), 2)
        self.assertEqual(executed_instructions[0][0], instruction1)
        self.assertEqual(executed_instructions[0][1], 3)  # Assuming ADD operation result
        self.assertEqual(executed_instructions[1][0], instruction2)
        self.assertEqual(executed_instructions[1][1], -1)  # Assuming SUB operation result
    
    def test_memory_access_stage(self):
        # Test case for the memory access stage
        # Create sample instructions and results
        instruction1 = Instruction(opcode='LOAD', operands=[1], destination=2)
        instruction2 = Instruction(opcode='STORE', operands=[3, 4], destination=None)
        
        # Set up the data cache
        self.data_cache.write(1, 10)
        
        # Access memory
        memory_results = self.memory_access_stage.access_memory([(instruction1, None), (instruction2, None)])
        
        # Assert the correctness of memory results
        self.assertEqual(len(memory_results), 2)
        self.assertEqual(memory_results[0][0], instruction1)
        self.assertEqual(memory_results[0][1], 10)  # Assuming the loaded value is 10
        self.assertEqual(memory_results[1][0], instruction2)
        self.assertIsNone(memory_results[1][1])  # Store instruction has no result
    
    def test_write_back_stage(self):
        # Test case for the write-back stage
        # Create sample instructions and results
        instruction1 = Instruction(opcode='ADD', operands=[1, 2], destination=3)
        instruction2 = Instruction(opcode='SUB', operands=[4, 5], destination=6)
        
        # Write back results
        self.write_back_stage.write_back([(instruction1, 10), (instruction2, 20)])
        
        # Assert the correctness of register file values
        self.assertEqual(self.register_file.read_register(3), 10)
        self.assertEqual(self.register_file.read_register(6), 20)

if __name__ == '__main__':
    unittest.main()