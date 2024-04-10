class Instruction:
    def __init__(self, opcode, operands, destination):
        self.opcode = opcode
        self.operands = operands
        self.destination = destination

    def __repr__(self):
        return f"Instruction(opcode={self.opcode}, operands={self.operands}, destination={self.destination})"

    def is_memory_operation(self):
        # Check if the instruction is a memory operation (e.g., load or store)
        # Return True if it is a memory operation, False otherwise
        pass

    def get_memory_address(self):
        # Return the memory address for memory operations
        # Return None for non-memory operations
        pass