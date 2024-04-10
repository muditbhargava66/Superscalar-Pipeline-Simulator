class DataCache:
    def __init__(self, cache_size, block_size, memory):
        self.cache_size = cache_size
        self.block_size = block_size
        self.memory = memory
        self.cache = {}

    def access(self, address):
        block_address = address // self.block_size
        block_offset = address % self.block_size

        if block_address in self.cache:
            # Cache hit
            return self.cache[block_address][block_offset]
        else:
            # Cache miss, fetch the block from memory
            block_data = self.fetch_block_from_memory(block_address)
            self.cache[block_address] = block_data
            return block_data[block_offset]

    def fetch_block_from_memory(self, block_address):
        start_address = block_address * self.block_size
        end_address = start_address + self.block_size
        block_data = self.memory[start_address:end_address]
        return block_data