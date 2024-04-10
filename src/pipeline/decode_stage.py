from utils.instruction import Instruction

class DecodeStage:
    def __init__(self, register_file):
        self.register_file = register_file

    def decode(self, instructions):
        decoded_instructions = []

        for instruction in instructions:
            # Decode the instruction
            decoded_instruction = self.decode_instruction(instruction)

            # Read the operand values from the register file
            self.read_operands(decoded_instruction)

            decoded_instructions.append(decoded_instruction)

        return decoded_instructions

    def decode_instruction(self, instruction):
        # Extract the opcode and operands from the instruction
        opcode = instruction.opcode
        operands = instruction.operands
        destination = instruction.destination  # Add this line to get the destination
        # Create a new Instruction object with the decoded information
        decoded_instruction = Instruction(instruction.pc, opcode, operands, destination)  # Include destination
        return decoded_instruction

    def read_operands(self, instruction):
        # Read the operand values from the register file
        operands = []
        for operand in instruction.operands:
            if self.is_register(operand):
                register_value = self.register_file.read_register(operand)
                operands.append(register_value)
            else:
                operands.append(operand)
        instruction.operands = operands

    def is_register(self, operand):
        # Check if the operand is a register
        # Assuming the register names are in the format 'r<number>'
        if isinstance(operand, str) and operand.startswith('r'):
            try:
                register_num = int(operand[1:])
                return 0 <= register_num < self.register_file.num_registers
            except ValueError:
                return False
        return False

class RegisterFile:
    def __init__(self, num_registers):
        self.num_registers = num_registers
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