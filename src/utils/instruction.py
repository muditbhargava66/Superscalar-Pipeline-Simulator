class Instruction:
    def __init__(self, opcode, operands, destination):
        self.opcode = opcode
        self.operands = operands
        self.destination = destination

    def __repr__(self):
        return f"Instruction(opcode={self.opcode}, operands={self.operands}, destination={self.destination})"

    def is_memory_operation(self):
        # Check if the instruction is a memory operation (e.g., load or store)
        # Implement your logic here based on the opcode or other instruction fields
        return self.opcode in ["LOAD", "STORE"]

    def get_memory_address(self):
        # Return the memory address for memory operations
        # Implement your logic here based on the operands or other instruction fields
        # Return None for non-memory operations
        if self.is_memory_operation():
            return self.operands[0]
        else:
            return None

    def is_branch(self):
        # Check if the instruction is a branch instruction
        # Implement your logic here based on the opcode or other instruction fields
        return self.opcode in ["BEQ", "BNE", "JMP"]

    def is_taken(self):
        # Check if the branch instruction is taken
        # Implement your logic here based on the operands or other instruction fields
        # Return True if the branch is taken, False otherwise
        # This is a placeholder implementation
        return True