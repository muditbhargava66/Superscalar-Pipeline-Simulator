class Cache:
    def __init__(self, cache_size, block_size):
        self.cache_size = cache_size
        self.block_size = block_size
        self.cache = {}

    def read(self, address):
        block_address = address // self.block_size
        block_offset = address % self.block_size

        if block_address in self.cache:
            return self.cache[block_address][block_offset]
        else:
            return None

    def write(self, address, data):
        block_address = address // self.block_size
        block_offset = address % self.block_size

        if block_address not in self.cache:
            self.cache[block_address] = [0] * self.block_size

        self.cache[block_address][block_offset] = data

    def load_block(self, block_address, block_data):
        self.cache[block_address] = block_data

class InstructionCache(Cache):
    def __init__(self, cache_size, block_size, fetch_bandwidth, memory):
        super().__init__(cache_size, block_size)
        self.fetch_bandwidth = fetch_bandwidth
        self.memory = memory

    def has_instruction(self, address):
        block_address = address // self.block_size
        return block_address in self.cache

    def fetch(self, address):
        instruction = self.read(address)
        if instruction is None:
            # Handle cache miss
            # Fetch the block from memory and load it into the cache
            block_address = address // self.block_size
            block_data = self.read_from_memory(block_address)
            self.load_block(block_address, block_data)
            instruction = self.read(address)
        return instruction

    def read_from_memory(self, block_address):
        start_address = block_address * self.block_size
        end_address = start_address + self.block_size
        block_data = self.memory[start_address:end_address]
        return block_data

class DataCache(Cache):
    def __init__(self, cache_size, block_size):
        super().__init__(cache_size, block_size)

    def load(self, address):
        data = self.read(address)
        if data is None:
            # Handle cache miss
            # Fetch the block from memory and load it into the cache
            block_address = address // self.block_size
            block_data = self.fetch_block_from_memory(block_address)
            self.load_block(block_address, block_data)
            data = self.read(address)
        return data

    def store(self, address, data):
        self.write(address, data)

    def fetch_block_from_memory(self, block_address):
        # Simulated memory access to fetch the block
        # Replace this with actual memory access logic
        block_data = [0] * self.block_size
        return block_data