"""
Memory Access Stage Implementation

This module implements the memory access stage of the pipeline, which handles
load and store operations to/from the data cache and main memory.
"""

from __future__ import annotations

import logging
from typing import Any

# Handle imports for both package and direct execution
try:
    from ..cache.cache import DataCache, Memory
    from ..utils.instruction import Instruction
except (ImportError, ValueError):
    import os
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    from cache.cache import DataCache, Memory
    from utils.instruction import Instruction


class MemoryAccessStage:
    """
    Memory access stage of the pipeline.
    
    Handles:
    - Load operations (reading from memory)
    - Store operations (writing to memory)
    - Cache access and miss handling
    - Memory disambiguation
    """

    def __init__(self, data_cache: DataCache, memory: Memory) -> None:
        """
        Initialize the memory access stage.
        
        Args:
            data_cache: Reference to the data cache
            memory: Reference to main memory
        """
        self.data_cache = data_cache
        self.memory = memory

        # Performance counters
        self.load_count = 0
        self.store_count = 0
        self.cache_hits = 0
        self.cache_misses = 0
        self.memory_stalls = 0

        # Store buffer for write buffering
        self.store_buffer: List[Tuple[int, Any]] = []
        self.store_buffer_size = 8

        logging.debug("Initialized Memory Access Stage")

    def access_memory(self, executed_instructions: List[Tuple[Instruction, Any]]) -> List[Tuple[Instruction, Any]]:
        """
        Process memory operations for executed instructions.
        
        Args:
            executed_instructions: List of (instruction, result) tuples from execute stage
            
        Returns:
            List of (instruction, result) tuples with memory operations completed
        """
        memory_results = []

        # Process store buffer first (write buffering)
        self._flush_store_buffer()

        for instruction, exec_result in executed_instructions:
            if instruction is None:
                continue

            try:
                if instruction.is_memory_operation():
                    # Handle memory operations
                    if instruction.is_load():
                        memory_result = self._handle_load(instruction, exec_result)
                        memory_results.append((instruction, memory_result))
                    elif instruction.is_store():
                        self._handle_store(instruction, exec_result)
                        memory_results.append((instruction, None))  # Stores don't produce results
                else:
                    # Non-memory instructions bypass this stage
                    memory_results.append((instruction, exec_result))

            except Exception as e:
                logging.error(f"Memory access error for {instruction}: {e}")
                # Mark instruction as failed
                instruction.status = "failed"
                memory_results.append((instruction, None))

        return memory_results

    def _handle_load(self, instruction: Instruction, address_calculation: Any) -> Any:
        """
        Handle load instruction.
        
        Args:
            instruction: Load instruction
            address_calculation: Result from execute stage (typically the address)
            
        Returns:
            Loaded data value
        """
        # Get memory address
        if isinstance(address_calculation, int):
            address = address_calculation
        else:
            # Extract address from instruction if not provided
            address = self._calculate_address(instruction)

        logging.debug(f"Load from address {address:#x}")

        # Check store buffer first (store-to-load forwarding)
        for store_addr, store_data in reversed(self.store_buffer):
            if store_addr == address:
                logging.debug(f"Store-to-load forwarding for address {address:#x}")
                return store_data

        # Check cache
        data = self.data_cache.get_data(address)

        if data is not None:
            # Cache hit
            self.cache_hits += 1
            logging.debug(f"Cache hit for address {address:#x}: {data}")
        else:
            # Cache miss - load from memory
            self.cache_misses += 1
            self.memory_stalls += 10  # Typical miss penalty

            try:
                # Read from main memory
                data = self.memory.read(address, 4)  # Read 4 bytes (word)
                if isinstance(data, list) and len(data) > 0:
                    data = data[0]

                # Add to cache
                self.data_cache.add_data(address, data)

                logging.debug(f"Cache miss for address {address:#x}, loaded {data} from memory")

            except Exception as e:
                logging.error(f"Memory read error at address {address:#x}: {e}")
                data = 0  # Default value on error

        self.load_count += 1
        instruction.status = "memory_complete"

        return data

    def _handle_store(self, instruction: Instruction, store_data: Any) -> None:
        """
        Handle store instruction.
        
        Args:
            instruction: Store instruction
            store_data: Data to store (from execute stage)
        """
        # Get memory address
        address = self._calculate_address(instruction)

        # Get data to store
        if store_data is None:
            # Extract from instruction if not provided
            if hasattr(instruction, 'register_values'):
                # Get the source register value
                source_regs = instruction.get_source_registers()
                if source_regs:
                    store_data = instruction.register_values.get(source_regs[-1], 0)
                else:
                    store_data = 0
            else:
                store_data = 0

        logging.debug(f"Store {store_data} to address {address:#x}")

        # Add to store buffer (write buffering)
        if len(self.store_buffer) >= self.store_buffer_size:
            # Buffer full, flush oldest entry
            self._flush_oldest_store()

        self.store_buffer.append((address, store_data))

        # Update cache (write-through policy)
        self.data_cache.add_data(address, store_data)

        self.store_count += 1
        instruction.status = "memory_complete"

    def _calculate_address(self, instruction: Instruction) -> int:
        """
        Calculate memory address for load/store instruction.
        
        Args:
            instruction: Memory instruction
            
        Returns:
            Calculated memory address
        """
        # For MIPS-style addressing: offset(base)
        # Instruction should have base address and offset

        if hasattr(instruction, 'memory_address'):
            return instruction.memory_address

        # Parse from operands
        if len(instruction.operands) >= 2:
            if instruction.is_load():
                # Load: lw $rt, offset($rs)
                # operands[1] contains offset(base)
                offset = 0
                base_addr = 0

                # Simple parsing - improve based on actual format
                if isinstance(instruction.operands[1], str) and '(' in instruction.operands[1]:
                    parts = instruction.operands[1].split('(')
                    offset = int(parts[0]) if parts[0] else 0
                    base_reg = parts[1].rstrip(')')

                    if hasattr(instruction, 'register_values'):
                        base_addr = instruction.register_values.get(base_reg, 0)
                elif isinstance(instruction.operands[1], int):
                    offset = instruction.operands[1]

                return base_addr + offset

            elif instruction.is_store():
                # Store: sw $rt, offset($rs)
                # Similar parsing
                return 0  # Placeholder

        # Default address
        return 0

    def _flush_store_buffer(self) -> None:
        """Flush entire store buffer to memory."""
        for address, data in self.store_buffer:
            try:
                self.memory.write(address, [data])
                logging.debug(f"Flushed store: {data} to address {address:#x}")
            except Exception as e:
                logging.error(f"Store buffer flush error at {address:#x}: {e}")

        self.store_buffer.clear()

    def _flush_oldest_store(self) -> None:
        """Flush oldest entry from store buffer."""
        if self.store_buffer:
            address, data = self.store_buffer.pop(0)
            try:
                self.memory.write(address, [data])
                logging.debug(f"Flushed oldest store: {data} to address {address:#x}")
            except Exception as e:
                logging.error(f"Store flush error at {address:#x}: {e}")

    def get_statistics(self) -> dict:
        """Get memory access stage statistics."""
        total_accesses = self.cache_hits + self.cache_misses
        hit_rate = (self.cache_hits / total_accesses * 100) if total_accesses > 0 else 0

        return {
            'load_count': self.load_count,
            'store_count': self.store_count,
            'total_memory_operations': self.load_count + self.store_count,
            'cache_hits': self.cache_hits,
            'cache_misses': self.cache_misses,
            'cache_hit_rate': hit_rate,
            'memory_stall_cycles': self.memory_stalls,
            'store_buffer_occupancy': len(self.store_buffer)
        }

    def reset(self) -> None:
        """Reset memory access stage."""
        self.load_count = 0
        self.store_count = 0
        self.cache_hits = 0
        self.cache_misses = 0
        self.memory_stalls = 0
        self.store_buffer.clear()

        logging.info("Memory access stage reset")


class AdvancedMemoryAccessStage(MemoryAccessStage):
    """
    Enhanced memory access stage with additional features.
    
    Adds:
    - Memory disambiguation
    - Prefetching support
    - Non-blocking cache support
    """

    def __init__(self, data_cache: DataCache, memory: Memory,
                 enable_prefetch: bool = True) -> None:
        super().__init__(data_cache, memory)
        self.enable_prefetch = enable_prefetch

        # Memory disambiguation table
        self.load_queue: List[Tuple[Instruction, int]] = []
        self.pending_loads: List[Tuple[Instruction, int, int]] = []  # (instruction, address, cycle)

        # Prefetch queue
        self.prefetch_queue: List[int] = []
        self.prefetch_distance = 4  # Prefetch 4 words ahead

    def access_memory(self, executed_instructions: List[Tuple[Instruction, Any]]) -> List[Tuple[Instruction, Any]]:
        """Enhanced memory access with disambiguation and prefetching."""
        memory_results = []

        # Process pending non-blocking loads
        self._process_pending_loads()

        # Process new instructions
        for instruction, exec_result in executed_instructions:
            if instruction is None:
                continue

            if instruction.is_memory_operation():
                if instruction.is_load():
                    # Check for memory dependencies
                    if self._check_memory_dependencies(instruction, exec_result):
                        # Add to load queue if dependencies exist
                        self.load_queue.append((instruction, exec_result))
                        continue

                    # Process load
                    memory_result = self._handle_load(instruction, exec_result)
                    memory_results.append((instruction, memory_result))

                    # Trigger prefetch if enabled
                    if self.enable_prefetch:
                        self._trigger_prefetch(exec_result)

                elif instruction.is_store():
                    self._handle_store(instruction, exec_result)
                    memory_results.append((instruction, None))

                    # Check if any queued loads can now proceed
                    self._check_load_queue()
            else:
                memory_results.append((instruction, exec_result))

        return memory_results

    def _check_memory_dependencies(self, load_instruction: Instruction,
                                  load_address: int) -> bool:
        """Check if load has dependencies on pending stores."""
        # Check store buffer for address conflicts
        for store_addr, _ in self.store_buffer:
            if store_addr == load_address:
                return True  # Dependency exists

        return False

    def _check_load_queue(self) -> None:
        """Check if queued loads can now proceed."""
        ready_loads = []
        remaining_loads = []

        for load_inst, load_addr in self.load_queue:
            if not self._check_memory_dependencies(load_inst, load_addr):
                ready_loads.append((load_inst, load_addr))
            else:
                remaining_loads.append((load_inst, load_addr))

        self.load_queue = remaining_loads

        # Process ready loads
        for load_inst, load_addr in ready_loads:
            self._handle_load(load_inst, load_addr)

    def _trigger_prefetch(self, current_address: int) -> None:
        """Trigger prefetch for future accesses."""
        prefetch_address = current_address + (self.prefetch_distance * 4)  # Word size

        if prefetch_address not in self.prefetch_queue:
            self.prefetch_queue.append(prefetch_address)

            # Initiate prefetch (non-blocking)
            if not self.data_cache.has_data(prefetch_address):
                # In real implementation, this would be non-blocking
                logging.debug(f"Prefetching address {prefetch_address:#x}")

    def _process_pending_loads(self) -> None:
        """Process non-blocking loads that may have completed."""
        # In a real implementation, this would check if memory requests completed
        # For simulation, we just track cycles
        completed_loads = []

        for i, (inst, addr, start_cycle) in enumerate(self.pending_loads):
            # Assume 10 cycle memory latency
            if start_cycle + 10 <= self.current_cycle:  # Need to track current cycle
                completed_loads.append(i)

        # Remove completed loads
        for i in reversed(completed_loads):
            self.pending_loads.pop(i)
