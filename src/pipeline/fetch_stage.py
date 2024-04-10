from utils.instruction import Instruction

class FetchStage:
    def __init__(self, instruction_cache, branch_predictor, memory):
        self.instruction_cache = instruction_cache
        self.branch_predictor = branch_predictor
        self.memory = memory
        self.pc = 0

    def fetch(self):
        instructions = []

        for _ in range(self.instruction_cache.fetch_bandwidth):
            if self.pc >= self.memory.size:  # Check if PC is within memory bounds
                break  # Stop fetching if PC is out of bounds

            if self.instruction_cache.has_instruction(self.pc):
                instruction_data = self.instruction_cache.get_instruction(self.pc)
                instruction = self.parse_instruction(instruction_data)
                instructions.append(instruction)
                self.pc += 4  # Assuming a 32-bit instruction size
            else:
                instruction_data = self.fetch_from_memory(self.pc)
                if instruction_data is not None:
                    instruction = self.parse_instruction(instruction_data)
                    instructions.append(instruction)
                    self.pc += 4  # Adjust PC as needed
                else:
                    # Handle the case where memory access fails
                    raise MemoryAccessError(f"Failed to fetch instruction at PC: {self.pc}")

        return instructions

    def fetch_from_memory(self, address):
        # Determine the block start and end addresses
        block_start_address = (address // self.instruction_cache.block_size) * self.instruction_cache.block_size
        block_end_address = block_start_address + self.instruction_cache.block_size

        # Check if the block end address is within the memory size
        if block_end_address <= self.memory.size:
            # Access the main memory and retrieve the block
            block_data = self.memory.read(block_start_address, block_end_address)

            # Parse the instruction data
            instruction_offset = address - block_start_address
            instruction_data = self.parse_instruction_data(block_data, instruction_offset)

            return instruction_data
        else:
            return None

    def parse_instruction_data(self, block_data, instruction_offset):
        # Parse the instruction data based on your instruction format
        # Example: Assuming a 32-bit instruction with opcode (8 bits), operand1 (8 bits), operand2 (8 bits), destination (8 bits)
        instruction_data = block_data[instruction_offset:instruction_offset + 4]
        opcode = instruction_data[0]
        operand1 = instruction_data[1]
        operand2 = instruction_data[2]
        destination = instruction_data[3]

        instruction_dict = {
            'opcode': opcode,
            'operands': [operand1, operand2],
            'destination': destination
        }

        return instruction_dict

    def parse_instruction(self, instruction_data):
        opcode = instruction_data['opcode']
        operands = instruction_data['operands']
        destination = instruction_data['destination']
        instruction = Instruction(self.pc, opcode, operands, destination)
        return instruction

    def update_pc(self, new_pc):
        self.pc = new_pc

    def get_pc(self):
        return self.pc

class InstructionCache:
    def __init__(self, cache_size, block_size, memory, fetch_bandwidth):
        self.cache_size = cache_size
        self.block_size = block_size
        self.memory = memory
        self.cache = {}
        self.fetch_bandwidth = fetch_bandwidth

    def has_instruction(self, address):
        block_address = address // self.block_size
        return block_address in self.cache

    def get_instruction(self, address):
        block_address = address // self.block_size
        block_offset = address % self.block_size
        if block_address in self.cache:
            return self.cache[block_address][block_offset]
        else:
            return None

class MemoryAccessError(Exception):
    pass