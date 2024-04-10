class Instruction:
    def __init__(self, pc, opcode, operands, destination=None):
        self.pc = pc
        self.opcode = opcode
        self.operands = operands if operands is not None else []
        self.destination = destination

    def __repr__(self):
        return f"Instruction(pc={self.pc}, opcode={self.opcode}, operands={self.operands}, destination={self.destination})"

    def is_memory_operation(self):
        return self.opcode in ["LOAD", "STORE"]

    def get_memory_address(self):
        if self.is_memory_operation() and len(self.operands) > 0:
            return self.operands[0]
        else:
            return None

    def is_branch(self):
        return self.opcode in ["BEQ", "BNE", "JMP"]

    def is_taken(self, register_file):
        if self.opcode == "BEQ":
            rs1 = register_file.read_register(self.operands[0])
            rs2 = register_file.read_register(self.operands[1])
            return rs1 == rs2
        elif self.opcode == "BNE":
            rs1 = register_file.read_register(self.operands[0])
            rs2 = register_file.read_register(self.operands[1])
            return rs1 != rs2
        elif self.opcode == "JMP":
            return True
        else:
            return False