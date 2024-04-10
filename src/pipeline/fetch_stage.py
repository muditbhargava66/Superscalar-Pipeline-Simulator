from utils.instruction import Instruction

class FetchStage:
    def __init__(self, instruction_cache, branch_predictor):
        self.instruction_cache = instruction_cache
        self.branch_predictor = branch_predictor
        self.pc = 0

    def fetch(self):
        instructions = []

        # Fetch multiple instructions from the instruction cache
        for _ in range(self.instruction_cache.fetch_bandwidth):
            # Check if the instruction cache has the requested instruction
            if self.instruction_cache.has_instruction(self.pc):
                # Fetch the instruction from the instruction cache
                instruction_data = self.instruction_cache.get_instruction(self.pc)
                instruction = Instruction(instruction_data)
                instructions.append(instruction)

                # Predict the next PC using the branch predictor
                predicted_pc = self.branch_predictor.predict(instruction)

                # Update the PC based on the branch prediction
                if predicted_pc is not None:
                    self.pc = predicted_pc
                else:
                    self.pc += 4  # Assuming a 32-bit instruction size
            else:
                # Instruction cache miss, fetch the instruction from memory
                instruction_data = self.fetch_from_memory(self.pc)
                if instruction_data is not None:
                    instruction = Instruction(instruction_data)
                    instructions.append(instruction)
                    self.pc += 4  # Assuming a 32-bit instruction size
                else:
                    # Memory access failed, handle accordingly (e.g., raise an exception)
                    raise MemoryAccessError(f"Failed to fetch instruction at PC: {self.pc}")

        return instructions

    def fetch_from_memory(self, address):
        # Simulate fetching the instruction from memory
        # Replace this with your memory access logic
        memory_data = self.instruction_cache.read_from_memory(address)
        return memory_data

    def update_pc(self, new_pc):
        self.pc = new_pc

    def get_pc(self):
        return self.pc

class InstructionCache:
    def __init__(self, cache_size, block_size, memory):
        self.cache_size = cache_size
        self.block_size = block_size
        self.memory = memory
        self.cache = {}

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

    def read_from_memory(self, address):
        # Simulate reading the instruction from memory
        # Replace this with your memory access logic
        if address < len(self.memory):
            return self.memory[address]
        else:
            return None

    @property
    def fetch_bandwidth(self):
        return 4  # Assuming a fetch bandwidth of 4 instructions per cycle

class MemoryAccessError(Exception):
    pass