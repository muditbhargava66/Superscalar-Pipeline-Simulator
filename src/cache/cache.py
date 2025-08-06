"""
Cache Implementation

This module implements various cache types for the superscalar pipeline simulator,
including instruction cache, data cache, and main memory.
"""

from __future__ import annotations

from collections import OrderedDict
import logging
import time
from typing import Any, Optional


class CacheBlock:
    """Represents a cache block with metadata."""

    def __init__(self, tag: int, data: List[Any], valid: bool = True) -> None:
        self.tag = tag
        self.data = data
        self.valid = valid
        self.dirty = False
        self.last_access_time = time.time()
        self.access_count = 0

    def access(self) -> None:
        """Update access metadata."""
        self.last_access_time = time.time()
        self.access_count += 1


class Cache:
    """
    Base cache implementation with configurable replacement policies.
    
    Supports:
    - Direct mapped, set associative, and fully associative configurations
    - LRU, FIFO, and random replacement policies
    - Write-through and write-back policies
    """

    def __init__(self, cache_size: int, block_size: int, associativity: int = 1,
                 replacement_policy: str = 'LRU', write_policy: str = 'write_through') -> None:
        """
        Initialize cache.
        
        Args:
            cache_size: Total cache size in bytes
            block_size: Size of each cache block in bytes
            associativity: Number of ways (1 = direct mapped, cache_size/block_size = fully associative)
            replacement_policy: 'LRU', 'FIFO', or 'random'
            write_policy: 'write_through' or 'write_back'
        """
        self.cache_size = cache_size
        self.block_size = block_size
        self.associativity = associativity
        self.replacement_policy = replacement_policy
        self.write_policy = write_policy

        # Calculate cache parameters
        self.num_blocks = cache_size // block_size
        self.num_sets = self.num_blocks // associativity
        self.index_bits = (self.num_sets - 1).bit_length()
        self.offset_bits = (block_size - 1).bit_length()

        # Initialize cache structure
        self.cache: Dict[int, List[Optional[CacheBlock]]] = {}
        for i in range(self.num_sets):
            self.cache[i] = [None] * associativity

        # Statistics
        self.hits = 0
        self.misses = 0
        self.evictions = 0
        self.writebacks = 0

        logging.debug(f"Initialized Cache: {cache_size}B, {block_size}B blocks, "
                     f"{associativity}-way, {replacement_policy}, {write_policy}")

    def _parse_address(self, address: int) -> Tuple[int, int, int]:
        """Parse address into tag, index, and offset."""
        offset = address & ((1 << self.offset_bits) - 1)
        index = (address >> self.offset_bits) & ((1 << self.index_bits) - 1)
        tag = address >> (self.offset_bits + self.index_bits)
        return tag, index, offset

    def _find_block(self, tag: int, index: int) -> Optional[Tuple[int, CacheBlock]]:
        """Find block in cache set."""
        cache_set = self.cache[index]
        for way, block in enumerate(cache_set):
            if block and block.valid and block.tag == tag:
                return way, block
        return None

    def _find_replacement_way(self, index: int) -> int:
        """Find way to replace using replacement policy."""
        cache_set = self.cache[index]

        # First, try to find an invalid block
        for way, block in enumerate(cache_set):
            if not block or not block.valid:
                return way

        # All blocks are valid, use replacement policy
        if self.replacement_policy == 'LRU':
            # Find least recently used
            lru_way = 0
            lru_time = cache_set[0].last_access_time
            for way, block in enumerate(cache_set):
                if block.last_access_time < lru_time:
                    lru_time = block.last_access_time
                    lru_way = way
            return lru_way

        elif self.replacement_policy == 'FIFO':
            # Find block with lowest access count (first in)
            fifo_way = 0
            min_count = cache_set[0].access_count
            for way, block in enumerate(cache_set):
                if block.access_count < min_count:
                    min_count = block.access_count
                    fifo_way = way
            return fifo_way

        else:  # Random
            import random
            return random.randint(0, self.associativity - 1)

    def read(self, address: int) -> Optional[Any]:
        """
        Read data from cache.
        
        Args:
            address: Memory address to read
            
        Returns:
            Data if hit, None if miss
        """
        tag, index, offset = self._parse_address(address)

        # Check for hit
        result = self._find_block(tag, index)
        if result:
            way, block = result
            block.access()
            self.hits += 1

            # Return data at offset
            if offset < len(block.data):
                return block.data[offset]
            else:
                return None

        # Cache miss
        self.misses += 1
        return None

    def write(self, address: int, data: Any) -> bool:
        """
        Write data to cache.
        
        Args:
            address: Memory address to write
            data: Data to write
            
        Returns:
            True if successful, False otherwise
        """
        tag, index, offset = self._parse_address(address)

        # Check for hit
        result = self._find_block(tag, index)
        if result:
            way, block = result
            block.access()

            # Update data
            if offset < len(block.data):
                block.data[offset] = data

                if self.write_policy == 'write_back':
                    block.dirty = True

                self.hits += 1
                return True

        # Cache miss - allocate new block for write
        self.misses += 1
        way = self._find_replacement_way(index)

        # Handle eviction
        old_block = self.cache[index][way]
        if old_block and old_block.valid:
            self.evictions += 1
            if old_block.dirty and self.write_policy == 'write_back':
                self.writebacks += 1
                # In real implementation, would write back to memory

        # Create new block
        new_data = [0] * self.block_size
        new_data[offset] = data
        new_block = CacheBlock(tag, new_data)

        if self.write_policy == 'write_back':
            new_block.dirty = True

        self.cache[index][way] = new_block
        return True

    def load_block(self, address: int, block_data: List[Any]) -> None:
        """Load a complete block into cache."""
        tag, index, offset = self._parse_address(address)
        way = self._find_replacement_way(index)

        # Handle eviction
        old_block = self.cache[index][way]
        if old_block and old_block.valid:
            self.evictions += 1
            if old_block.dirty and self.write_policy == 'write_back':
                self.writebacks += 1

        # Load new block
        new_block = CacheBlock(tag, block_data[:self.block_size])
        self.cache[index][way] = new_block

    def invalidate(self, address: int) -> None:
        """Invalidate cache block containing address."""
        tag, index, offset = self._parse_address(address)
        result = self._find_block(tag, index)
        if result:
            way, block = result
            block.valid = False

    def flush(self) -> None:
        """Flush all dirty blocks and invalidate cache."""
        for index in range(self.num_sets):
            for way in range(self.associativity):
                block = self.cache[index][way]
                if block and block.valid and block.dirty:
                    self.writebacks += 1
                    # In real implementation, would write back to memory
                self.cache[index][way] = None

    def get_hit_rate(self) -> float:
        """Get cache hit rate as percentage."""
        total_accesses = self.hits + self.misses
        return (self.hits / total_accesses * 100) if total_accesses > 0 else 0.0

    def get_statistics(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_accesses = self.hits + self.misses
        return {
            'hits': self.hits,
            'misses': self.misses,
            'total_accesses': total_accesses,
            'hit_rate': self.get_hit_rate(),
            'evictions': self.evictions,
            'writebacks': self.writebacks,
            'cache_size': self.cache_size,
            'block_size': self.block_size,
            'associativity': self.associativity,
            'num_sets': self.num_sets
        }

    def reset_statistics(self) -> None:
        """Reset cache statistics."""
        self.hits = 0
        self.misses = 0
        self.evictions = 0
        self.writebacks = 0

class InstructionCache(Cache):
    """
    Instruction cache specialized for fetching instructions.
    
    Features:
    - Instruction-specific fetch bandwidth
    - Integration with memory hierarchy
    - Prefetching support
    """

    def __init__(self, cache_size: int, block_size: int, memory: Memory,
                 fetch_bandwidth: int = 4, associativity: int = 4) -> None:
        """
        Initialize instruction cache.
        
        Args:
            cache_size: Cache size in bytes
            block_size: Block size in bytes
            memory: Reference to main memory
            fetch_bandwidth: Number of instructions that can be fetched per cycle
            associativity: Cache associativity
        """
        super().__init__(cache_size, block_size, associativity)
        self.fetch_bandwidth = fetch_bandwidth
        self.memory = memory

        # Instruction-specific storage
        self.instruction_storage: Dict[int, Any] = {}

        # Prefetch state
        self.prefetch_enabled = True
        self.prefetch_distance = 2  # Prefetch 2 blocks ahead

        logging.debug(f"Initialized Instruction Cache: {cache_size}B, "
                     f"fetch bandwidth: {fetch_bandwidth}")

    def has_instruction(self, address: int) -> bool:
        """Check if instruction is in cache."""
        # Check both cache structure and instruction storage
        if address in self.instruction_storage:
            return True

        # Check cache blocks
        tag, index, offset = self._parse_address(address)
        result = self._find_block(tag, index)
        return result is not None

    def get_instruction(self, address: int) -> Optional[Dict[str, Any]]:
        """
        Get instruction from cache.
        
        Args:
            address: Instruction address
            
        Returns:
            Instruction data dictionary or None if miss
        """
        # First check instruction storage
        if address in self.instruction_storage:
            self.hits += 1
            return self.instruction_storage[address]

        # Check cache blocks
        data = self.read(address)
        if data is not None:
            return data

        # Cache miss
        self.misses += 1
        return None

    def add_instruction(self, address: int, instruction_data: Dict[str, Any]) -> None:
        """
        Add instruction to cache.
        
        Args:
            address: Instruction address
            instruction_data: Instruction data dictionary
        """
        # Store in instruction storage for quick access
        self.instruction_storage[address] = instruction_data

        # Also store in cache structure
        self.write(address, instruction_data)

        # Trigger prefetch if enabled
        if self.prefetch_enabled:
            self._prefetch(address)

    def fetch_instructions(self, start_address: int, count: int) -> List[Optional[Dict[str, Any]]]:
        """
        Fetch multiple instructions starting from address.
        
        Args:
            start_address: Starting address
            count: Number of instructions to fetch (limited by bandwidth)
            
        Returns:
            List of instruction data dictionaries
        """
        instructions = []
        actual_count = min(count, self.fetch_bandwidth)

        for i in range(actual_count):
            address = start_address + (i * 4)  # Assume 4-byte instructions
            instruction = self.get_instruction(address)
            instructions.append(instruction)

            # If we hit a miss, might need to fetch from memory
            if instruction is None:
                # In real implementation, would fetch block from memory
                pass

        return instructions

    def _prefetch(self, address: int) -> None:
        """
        Prefetch instructions ahead of current address.
        
        Args:
            address: Current instruction address
        """
        for i in range(1, self.prefetch_distance + 1):
            prefetch_addr = address + (i * self.block_size)

            # Only prefetch if not already in cache
            if not self.has_instruction(prefetch_addr):
                # In real implementation, would initiate memory fetch
                logging.debug(f"Prefetching block at address {prefetch_addr:#x}")

    def invalidate_range(self, start_address: int, end_address: int) -> None:
        """Invalidate instruction cache range (for self-modifying code)."""
        for address in range(start_address, end_address, 4):
            if address in self.instruction_storage:
                del self.instruction_storage[address]
            self.invalidate(address)

class DataCache(Cache):
    """
    Data cache for load/store operations.
    
    Features:
    - Load/store interface
    - Write buffer support
    - Memory coherence protocols
    """

    def __init__(self, cache_size: int, block_size: int, associativity: int = 4,
                 write_policy: str = 'write_back') -> None:
        """
        Initialize data cache.
        
        Args:
            cache_size: Cache size in bytes
            block_size: Block size in bytes
            associativity: Cache associativity
            write_policy: 'write_through' or 'write_back'
        """
        super().__init__(cache_size, block_size, associativity,
                        write_policy=write_policy)

        # Write buffer for write-through policy
        self.write_buffer: List[Tuple[int, Any]] = []
        self.write_buffer_size = 8

        # Store buffer for write-back policy
        self.store_buffer: OrderedDict[int, Any] = OrderedDict()
        self.store_buffer_size = 16

        logging.debug(f"Initialized Data Cache: {cache_size}B, {write_policy}")

    def load(self, address: int) -> Optional[Any]:
        """
        Load data from cache/memory.
        
        Args:
            address: Memory address to load from
            
        Returns:
            Data value or None if not found
        """
        # First check store buffer for most recent value
        if address in self.store_buffer:
            return self.store_buffer[address]

        # Check cache
        data = self.read(address)
        if data is not None:
            return data

        # Cache miss - would fetch from memory in real implementation
        self.misses += 1
        return None

    def store(self, address: int, data: Any) -> bool:
        """
        Store data to cache/memory.
        
        Args:
            address: Memory address to store to
            data: Data to store
            
        Returns:
            True if successful
        """
        # Add to store buffer
        if len(self.store_buffer) >= self.store_buffer_size:
            # Remove oldest entry
            self.store_buffer.popitem(last=False)

        self.store_buffer[address] = data

        # Write to cache
        success = self.write(address, data)

        # Handle write buffer for write-through
        if self.write_policy == 'write_through':
            if len(self.write_buffer) >= self.write_buffer_size:
                # Flush oldest write
                self.write_buffer.pop(0)

            self.write_buffer.append((address, data))

        return success

    def has_data(self, address: int) -> bool:
        """Check if data is available (cache or store buffer)."""
        if address in self.store_buffer:
            return True

        return self.read(address) is not None

    def get_data(self, address: int) -> Optional[Any]:
        """Get data with hit/miss tracking."""
        return self.load(address)

    def add_data(self, address: int, data: Any) -> None:
        """Add data to cache."""
        self.store(address, data)

    def flush_write_buffer(self) -> None:
        """Flush write buffer to memory."""
        if self.write_policy == 'write_through':
            # In real implementation, would write to memory
            flushed = len(self.write_buffer)
            self.write_buffer.clear()
            logging.debug(f"Flushed {flushed} writes from write buffer")

    def flush_store_buffer(self) -> None:
        """Flush store buffer."""
        flushed = len(self.store_buffer)
        self.store_buffer.clear()
        logging.debug(f"Flushed {flushed} entries from store buffer")

    def get_hits(self) -> int:
        """Get hit count."""
        return self.hits

    def get_misses(self) -> int:
        """Get miss count."""
        return self.misses

class Memory:
    """
    Main memory implementation with realistic access patterns.
    
    Features:
    - Configurable access latency
    - Bandwidth limitations
    - Memory access statistics
    """

    def __init__(self, size: int, access_latency: int = 100, bandwidth: int = 8) -> None:
        """
        Initialize memory.
        
        Args:
            size: Memory size in bytes
            access_latency: Access latency in cycles
            bandwidth: Memory bandwidth in bytes per cycle
        """
        self.size = size
        self.access_latency = access_latency
        self.bandwidth = bandwidth
        self.data = [0] * size

        # Statistics
        self.read_count = 0
        self.write_count = 0
        self.bytes_read = 0
        self.bytes_written = 0

        # Access queue for modeling bandwidth limits
        self.pending_accesses: List[Tuple[str, int, int]] = []  # (type, address, size)

        logging.debug(f"Initialized Memory: {size}B, {access_latency} cycle latency, "
                     f"{bandwidth}B/cycle bandwidth")

    def read(self, address: int, size: int = 4) -> Any:
        """
        Read data from memory.
        
        Args:
            address: Starting address
            size: Number of bytes to read
            
        Returns:
            Data value or list of values
        """
        if address + size > self.size:
            raise MemoryAccessError(
                f"Memory read out of range: {address + size} > {self.size}"
            )

        # Update statistics
        self.read_count += 1
        self.bytes_read += size

        # Add to pending accesses (for bandwidth modeling)
        self.pending_accesses.append(('read', address, size))

        # Return data
        if size == 1:
            return self.data[address]
        else:
            return self.data[address:address + size]

    def write(self, address: int, data: Any, size: int = None) -> None:
        """
        Write data to memory.
        
        Args:
            address: Starting address
            data: Data to write (single value or list)
            size: Size in bytes (inferred if not provided)
        """
        if isinstance(data, list):
            actual_size = len(data)
            if address + actual_size > self.size:
                raise MemoryAccessError(
                    f"Memory write out of range: {address + actual_size} > {self.size}"
                )
            self.data[address:address + actual_size] = data
        else:
            actual_size = size or 4  # Default to 4 bytes
            if address + actual_size > self.size:
                raise MemoryAccessError(
                    f"Memory write out of range: {address + actual_size} > {self.size}"
                )

            if actual_size == 1:
                self.data[address] = data
            else:
                # For multi-byte writes, replicate the value
                for i in range(actual_size):
                    self.data[address + i] = data

        # Update statistics
        self.write_count += 1
        self.bytes_written += actual_size

        # Add to pending accesses
        self.pending_accesses.append(('write', address, actual_size))

    def read_block(self, address: int, block_size: int) -> List[Any]:
        """Read a complete cache block."""
        return self.read(address, block_size)

    def write_block(self, address: int, block_data: List[Any]) -> None:
        """Write a complete cache block."""
        self.write(address, block_data)

    def is_address_valid(self, address: int) -> bool:
        """Check if address is within memory bounds."""
        return 0 <= address < self.size

    def get_access_latency(self, address: int, size: int) -> int:
        """
        Calculate access latency based on size and bandwidth.
        
        Args:
            address: Memory address
            size: Access size in bytes
            
        Returns:
            Latency in cycles
        """
        # Base latency plus bandwidth-limited transfer time
        transfer_cycles = (size + self.bandwidth - 1) // self.bandwidth
        return self.access_latency + transfer_cycles

    def update_cycle(self) -> None:
        """Update memory state for one cycle (process pending accesses)."""
        # Process bandwidth-limited accesses
        bytes_processed = 0
        remaining_accesses = []

        for access_type, address, size in self.pending_accesses:
            if bytes_processed + size <= self.bandwidth:
                bytes_processed += size
                # Access completed this cycle
            else:
                # Access must wait for next cycle
                remaining_accesses.append((access_type, address, size))

        self.pending_accesses = remaining_accesses

    def get_statistics(self) -> Dict[str, Any]:
        """Get memory access statistics."""
        total_accesses = self.read_count + self.write_count
        total_bytes = self.bytes_read + self.bytes_written

        return {
            'total_accesses': total_accesses,
            'read_count': self.read_count,
            'write_count': self.write_count,
            'bytes_read': self.bytes_read,
            'bytes_written': self.bytes_written,
            'total_bytes': total_bytes,
            'average_access_size': total_bytes / total_accesses if total_accesses > 0 else 0,
            'pending_accesses': len(self.pending_accesses),
            'memory_utilization': (total_bytes / self.size) * 100
        }

    def reset_statistics(self) -> None:
        """Reset memory statistics."""
        self.read_count = 0
        self.write_count = 0
        self.bytes_read = 0
        self.bytes_written = 0
        self.pending_accesses.clear()

    def dump_region(self, start_address: int, size: int) -> List[Any]:
        """Dump memory region for debugging."""
        if start_address + size > self.size:
            size = self.size - start_address

        return self.data[start_address:start_address + size]

    def load_program(self, program_data: List[Any], start_address: int = 0) -> None:
        """Load program data into memory."""
        if start_address + len(program_data) > self.size:
            raise MemoryAccessError("Program too large for memory")

        self.data[start_address:start_address + len(program_data)] = program_data
        logging.info(f"Loaded {len(program_data)} bytes at address {start_address:#x}")


class MemoryAccessError(Exception):
    """Exception raised for memory access errors."""
    pass


class MemoryHierarchy:
    """
    Complete memory hierarchy with L1, L2 caches and main memory.
    
    Provides unified interface for memory operations with realistic
    latencies and bandwidth constraints.
    """

    def __init__(self, memory_size: int = 1024*1024,
                 l1_i_size: int = 32*1024, l1_d_size: int = 32*1024,
                 l2_size: int = 256*1024, block_size: int = 64) -> None:
        """
        Initialize memory hierarchy.
        
        Args:
            memory_size: Main memory size
            l1_i_size: L1 instruction cache size
            l1_d_size: L1 data cache size
            l2_size: L2 unified cache size
            block_size: Cache block size
        """
        # Main memory
        self.memory = Memory(memory_size)

        # L2 unified cache
        self.l2_cache = Cache(l2_size, block_size, associativity=8)

        # L1 caches
        self.l1_i_cache = InstructionCache(l1_i_size, block_size, self.memory)
        self.l1_d_cache = DataCache(l1_d_size, block_size)

        # Hierarchy statistics
        self.l1_i_accesses = 0
        self.l1_d_accesses = 0
        self.l2_accesses = 0
        self.memory_accesses = 0

        logging.info(f"Initialized Memory Hierarchy: "
                    f"L1I={l1_i_size}B, L1D={l1_d_size}B, L2={l2_size}B, "
                    f"Memory={memory_size}B")

    def read_instruction(self, address: int) -> Optional[Dict[str, Any]]:
        """Read instruction through cache hierarchy."""
        self.l1_i_accesses += 1

        # Try L1 instruction cache
        instruction = self.l1_i_cache.get_instruction(address)
        if instruction is not None:
            return instruction

        # L1 miss - try L2
        self.l2_accesses += 1
        l2_data = self.l2_cache.read(address)
        if l2_data is not None:
            # Load into L1
            self.l1_i_cache.add_instruction(address, l2_data)
            return l2_data

        # L2 miss - access memory
        self.memory_accesses += 1
        # In real implementation, would fetch from memory
        return None

    def read_data(self, address: int) -> Optional[Any]:
        """Read data through cache hierarchy."""
        self.l1_d_accesses += 1

        # Try L1 data cache
        data = self.l1_d_cache.load(address)
        if data is not None:
            return data

        # L1 miss - try L2
        self.l2_accesses += 1
        l2_data = self.l2_cache.read(address)
        if l2_data is not None:
            # Load into L1
            self.l1_d_cache.add_data(address, l2_data)
            return l2_data

        # L2 miss - access memory
        self.memory_accesses += 1
        return self.memory.read(address)

    def write_data(self, address: int, data: Any) -> bool:
        """Write data through cache hierarchy."""
        self.l1_d_accesses += 1

        # Write to L1 data cache
        success = self.l1_d_cache.store(address, data)

        # Also update L2 if present
        if self.l2_cache.read(address) is not None:
            self.l2_cache.write(address, data)

        # Write-through to memory (simplified)
        self.memory.write(address, data)

        return success

    def get_hierarchy_statistics(self) -> Dict[str, Any]:
        """Get complete hierarchy statistics."""
        return {
            'l1_instruction': self.l1_i_cache.get_statistics(),
            'l1_data': self.l1_d_cache.get_statistics(),
            'l2_unified': self.l2_cache.get_statistics(),
            'main_memory': self.memory.get_statistics(),
            'access_counts': {
                'l1_i_accesses': self.l1_i_accesses,
                'l1_d_accesses': self.l1_d_accesses,
                'l2_accesses': self.l2_accesses,
                'memory_accesses': self.memory_accesses
            }
        }
