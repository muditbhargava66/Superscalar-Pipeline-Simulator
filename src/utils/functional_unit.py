class FunctionalUnit:
    def __init__(self, id, supported_opcodes):
        self.id = id
        self.supported_opcodes = supported_opcodes
        self.busy = False
        self.remaining_cycles = 0

    def is_free(self):
        return not self.busy

    def can_execute(self, opcode):
        return opcode in self.supported_opcodes

    def execute(self, instruction, register_file):
        if not self.can_execute(instruction.opcode):
            raise ValueError(f"Unsupported opcode '{instruction.opcode}' for functional unit {self.id}")

        if instruction.opcode == "ADD":
            rs1 = register_file.read_register(instruction.operands[0])
            rs2 = register_file.read_register(instruction.operands[1])
            result = rs1 + rs2
        elif instruction.opcode == "SUB":
            rs1 = register_file.read_register(instruction.operands[0])
            rs2 = register_file.read_register(instruction.operands[1])
            result = rs1 - rs2
        elif instruction.opcode == "MUL":
            rs1 = register_file.read_register(instruction.operands[0])
            rs2 = register_file.read_register(instruction.operands[1])
            result = rs1 * rs2
        elif instruction.opcode == "DIV":
            rs1 = register_file.read_register(instruction.operands[0])
            rs2 = register_file.read_register(instruction.operands[1])
            if rs2 != 0:
                result = rs1 // rs2
            else:
                raise ValueError("Division by zero")
        else:
            raise ValueError(f"Unsupported opcode '{instruction.opcode}' for execution")

        self.busy = True
        self.remaining_cycles = self.get_execution_latency(instruction.opcode)
        return result

    def update(self):
        if self.busy:
            self.remaining_cycles -= 1
            if self.remaining_cycles <= 0:
                self.busy = False

    def get_execution_latency(self, opcode):
        latencies = {
            "ADD": 2,
            "SUB": 2,
            "MUL": 4,
            "DIV": 8
        }
        return latencies.get(opcode, 1)