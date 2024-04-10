from utils.instruction import Instruction

class MemoryAccessStage:
    def __init__(self, data_cache):
        self.data_cache = data_cache

    def access_memory(self, executed_instructions):
        memory_results = []

        for instruction, result in executed_instructions:
            if instruction.is_memory_operation():
                # Access the data cache for memory operations
                memory_result = self.data_cache.access(instruction.memory_address)
                memory_results.append((instruction, memory_result))
            else:
                # Non-memory instructions bypass the memory access stage
                memory_results.append((instruction, result))

        return memory_results