from utils.instruction import Instruction

class DecodeStage:
    def __init__(self, register_file):
        self.register_file = register_file

    def decode(self, instructions):
        decoded_instructions = []

        for instruction in instructions:
            # Decode the instruction
            opcode, operands = self.decode_instruction(instruction)

            # Create a new Instruction object with the decoded information
            decoded_instruction = Instruction(instruction.pc, opcode, operands)

            # Read the operand values from the register file
            self.read_operands(decoded_instruction)

            decoded_instructions.append(decoded_instruction)

        return decoded_instructions

    def decode_instruction(self, instruction):
        # Extract the opcode and operands from the instruction
        # Replace this with your actual decoding logic based on your instruction format
        opcode = instruction.data & 0xFF  # Assuming opcode is the first byte
        operand1 = (instruction.data >> 8) & 0xFF  # Assuming operand1 is the second byte
        operand2 = (instruction.data >> 16) & 0xFF  # Assuming operand2 is the third byte
        operands = [operand1, operand2]

        return opcode, operands

    def read_operands(self, instruction):
        # Read the operand values from the register file
        for i, operand in enumerate(instruction.operands):
            if self.is_register(operand):
                register_value = self.register_file.read_register(operand)
                instruction.operands[i] = register_value

    def is_register(self, operand):
        # Check if the operand is a register
        # Replace this with your actual logic to determine if an operand is a register
        return True  # Assuming all operands are registers for simplicity

class RegisterFile:
    def __init__(self, num_registers):
        self.registers = [0] * num_registers

    def read_register(self, register_num):
        if 0 <= register_num < len(self.registers):
            return self.registers[register_num]
        else:
            raise InvalidRegisterException(f"Invalid register number: {register_num}")

    def write_register(self, register_num, value):
        if 0 <= register_num < len(self.registers):
            self.registers[register_num] = value
        else:
            raise InvalidRegisterException(f"Invalid register number: {register_num}")

class InvalidRegisterException(Exception):
    pass