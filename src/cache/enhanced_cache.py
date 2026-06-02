#!/usr/bin/env python3

"""
Enhanced Cache System with Realistic Timing

This module provides cycle-accurate cache simulation with proper
timing models, replacement policies, and performance tracking.
"""

from enum import Enum
import logging
import time
from typing import Any, List, Optional, Type


class CacheState(Enum):
    """Cache line states for coherence protocol."""

    INVALID = "invalid"
    VALID = "valid"
    DIRTY = "dirty"


class ReplacementPolicy(Enum):
    """Cache replacement policies."""

    LRU = "lru"
    FIFO = "fifo"
    RANDOM = "random"


class MemoryAccessType(Enum):
    """Types of memory access."""

    READ = "read"
    WRITE = "write"
    INSTRUCTION_FETCH = "instruction_fetch"


class CacheLine:
    """Represents a cache line with timing and state information."""

    def __init__(self, tag: int, data: int, valid: bool = True):
        self.tag = tag
        self.data = data
        self.valid = valid
        self.dirty = False
        self.last_access_time = 0
        self.access_count = 0
        self.state = CacheState.VALID


class MemoryRequest:
    """Represents a memory request with timing information."""

    def __init__(
        self,
        address: int,
        access_type: MemoryAccessType,
        data: int | None = None,
        request_id: int = 0,
    ):
        self.address = address
        self.access_type = access_type
        self.data = data
        self.request_id = request_id
        self.start_cycle = 0
        self.completion_cycle = 0
        self.cache_hit = False
        self.cache_level = 0


class EnhancedCache:
    """
    Enhanced cache with cycle-accurate timing and realistic behavior.

    Features:
    - Configurable timing parameters
    - Multiple replacement policies
    - Write-back and write-through support
    - Miss status holding registers (MSHRs)
    - Performance tracking and statistics
    """

    def __init__(
        self,
        cache_size: int = 32768,
        block_size: int = 64,
        associativity: int = 4,
        replacement_policy: ReplacementPolicy = ReplacementPolicy.LRU,
        write_policy: str = "write_back",
        hit_latency: int = 1,
        miss_penalty: int = 10,
        mshr_entries: int = 4,
    ):
        """
        Initialize enhanced cache.

        Args:
            cache_size: Total cache size in bytes
            block_size: Cache block size in bytes
            associativity: Number of ways
            replacement_policy: Replacement policy to use
            write_policy: "write_back" or "write_through"
            hit_latency: Cycles for cache hit
            miss_penalty: Additional cycles for cache miss
            mshr_entries: Number of MSHR entries
        """
        self.cache_size = cache_size
        self.block_size = block_size
        self.associativity = associativity
        self.replacement_policy = replacement_policy
        self.write_policy = write_policy
        self.hit_latency = hit_latency
        self.miss_penalty = miss_penalty
        self.mshr_entries = mshr_entries

        # Calculate cache parameters
        self.num_sets = cache_size // (block_size * associativity)
        self.index_bits = (self.num_sets - 1).bit_length()
        self.offset_bits = (block_size - 1).bit_length()
        self.tag_bits = 32 - self.index_bits - self.offset_bits

        # Initialize cache structure
        self.cache: list[list[CacheLine | None]] = [
            [None for _ in range(associativity)] for _ in range(self.num_sets)
        ]

        # Miss Status Holding Registers
        self.mshrs: dict[int, MemoryRequest] = {}
        self.pending_requests: list[MemoryRequest] = []

        # Timing and statistics
        self.current_cycle = 0
        self.stats = {
            "total_accesses": 0,
            "hits": 0,
            "misses": 0,
            "writebacks": 0,
            "mshr_hits": 0,
            "mshr_misses": 0,
            "average_access_time": 0.0,
            "hit_rate": 0.0,
            "miss_rate": 0.0,
            "cycles_stalled": 0,
        }

        # LRU tracking
        self.lru_counters: list[list[int]] = [
            [0 for _ in range(associativity)] for _ in range(self.num_sets)
        ]

        self.logger = logging.getLogger(__name__)

    def access(
        self,
        address: int,
        access_type: MemoryAccessType,
        data: int | None = None,
        request_id: int = 0,
    ) -> tuple[bool, int, int | None]:
        """
        Access cache with cycle-accurate timing.

        Args:
            address: Memory address to access
            access_type: Type of memory access
            data: Data to write (for write operations)
            request_id: Unique request identifier

        Returns:
            (hit, cycles_taken, data) tuple
        """
        self.stats["total_accesses"] += 1

        # Parse address
        tag, index, offset = self._parse_address(address)

        # Check for pending MSHR request
        if address in self.mshrs:
            self.stats["mshr_hits"] += 1
            return False, self.miss_penalty, None  # Still waiting

        # Check cache for hit
        hit_way = self._find_cache_line(index, tag)

        if hit_way is not None:
            # Cache hit
            return self._handle_cache_hit(index, hit_way, access_type, data)
        else:
            # Cache miss
            return self._handle_cache_miss(
                address, index, tag, access_type, data, request_id
            )

    def advance_cycle(self) -> list[MemoryRequest]:
        """
        Advance cache by one cycle and process pending requests.

        Returns:
            List of completed memory requests
        """
        self.current_cycle += 1
        completed_requests = []

        # Process pending MSHR requests
        for addr, request in list(self.mshrs.items()):
            if self.current_cycle >= request.completion_cycle:
                # Request completed
                completed_requests.append(request)
                del self.mshrs[addr]

                # Install cache line
                tag, index, offset = self._parse_address(addr)
                victim_way = self._select_victim(index)

                # Handle writeback if necessary
                if (
                    self.cache[index][victim_way] is not None
                    and self.cache[index][victim_way].dirty  # type: ignore[union-attr]
                ):
                    self.stats["writebacks"] += 1

                # Install new line
                self.cache[index][victim_way] = CacheLine(tag, request.data or 0)
                self._update_lru(index, victim_way)

        return completed_requests

    def _handle_cache_hit(
        self, index: int, way: int, access_type: MemoryAccessType, data: int | None
    ) -> tuple[bool, int, int | None]:
        """Handle cache hit."""
        self.stats["hits"] += 1
        cache_line = self.cache[index][way]

        # Update access information
        cache_line.last_access_time = self.current_cycle  # type: ignore[union-attr]
        cache_line.access_count += 1  # type: ignore[union-attr]
        self._update_lru(index, way)

        if access_type == MemoryAccessType.WRITE:
            if data is not None:
                cache_line.data = data  # type: ignore[union-attr]
                if self.write_policy == "write_back":
                    cache_line.dirty = True  # type: ignore[union-attr]
                # Write-through would also write to next level

        return True, self.hit_latency, cache_line.data  # type: ignore[union-attr]

    def _handle_cache_miss(
        self,
        address: int,
        index: int,
        tag: int,
        access_type: MemoryAccessType,
        data: int | None,
        request_id: int,
    ) -> tuple[bool, int, int | None]:
        """Handle cache miss."""
        self.stats["misses"] += 1

        # Check MSHR availability
        if len(self.mshrs) >= self.mshr_entries:
            self.stats["mshr_misses"] += 1
            self.stats["cycles_stalled"] += 1
            return False, 1, None  # Stall for one cycle

        # Allocate MSHR entry
        request = MemoryRequest(address, access_type, data, request_id)
        request.start_cycle = self.current_cycle
        request.completion_cycle = self.current_cycle + self.miss_penalty
        request.cache_hit = False

        self.mshrs[address] = request

        return False, self.miss_penalty, None

    def _find_cache_line(self, index: int, tag: int) -> int | None:
        """Find cache line in set, return way number if found."""
        for way in range(self.associativity):
            line = self.cache[index][way]
            if line is not None and line.valid and line.tag == tag:
                return way
        return None

    def _select_victim(self, index: int) -> int:
        """Select victim way for replacement."""
        # First, try to find an invalid line
        for way in range(self.associativity):
            if self.cache[index][way] is None or not self.cache[index][way].valid:  # type: ignore[union-attr]
                return way

        # All lines valid, use replacement policy
        if self.replacement_policy == ReplacementPolicy.LRU:
            return self._select_lru_victim(index)
        elif self.replacement_policy == ReplacementPolicy.FIFO:
            return self._select_fifo_victim(index)
        else:  # RANDOM
            import random

            return random.randint(0, self.associativity - 1)

    def _select_lru_victim(self, index: int) -> int:
        """Select LRU victim."""
        min_counter = min(self.lru_counters[index])
        return self.lru_counters[index].index(min_counter)

    def _select_fifo_victim(self, index: int) -> int:
        """Select FIFO victim (simplified as oldest access time)."""
        oldest_time = float("inf")
        victim_way = 0

        for way in range(self.associativity):
            line = self.cache[index][way]
            if line and line.last_access_time < oldest_time:
                oldest_time = line.last_access_time
                victim_way = way

        return victim_way

    def _update_lru(self, index: int, way: int) -> None:
        """Update LRU counters."""
        if self.replacement_policy == ReplacementPolicy.LRU:
            # Increment all counters
            for i in range(self.associativity):
                self.lru_counters[index][i] += 1
            # Reset accessed way to 0
            self.lru_counters[index][way] = 0

    def _parse_address(self, address: int) -> tuple[int, int, int]:
        """Parse address into tag, index, and offset."""
        offset = address & ((1 << self.offset_bits) - 1)
        index = (address >> self.offset_bits) & ((1 << self.index_bits) - 1)
        tag = address >> (self.offset_bits + self.index_bits)
        return tag, index, offset

    def invalidate_line(self, address: int) -> bool:
        """Invalidate cache line containing address."""
        tag, index, offset = self._parse_address(address)
        way = self._find_cache_line(index, tag)

        if way is not None:
            self.cache[index][way].valid = False  # type: ignore[union-attr]
            self.cache[index][way].state = CacheState.INVALID  # type: ignore[union-attr]
            return True
        return False

    def flush_cache(self) -> int:
        """Flush all dirty lines to next level."""
        writebacks = 0

        for set_idx in range(self.num_sets):
            for way in range(self.associativity):
                line = self.cache[set_idx][way]
                if line and line.valid and line.dirty:
                    # Writeback (simplified)
                    writebacks += 1
                    line.dirty = False

        self.stats["writebacks"] += writebacks
        return writebacks

    def get_statistics(self) -> dict[str, Any]:
        """Get cache statistics."""
        total = self.stats["total_accesses"]
        if total > 0:
            self.stats["hit_rate"] = self.stats["hits"] / total
            self.stats["miss_rate"] = self.stats["misses"] / total
            self.stats["average_access_time"] = (
                self.stats["hits"] * self.hit_latency
                + self.stats["misses"] * (self.hit_latency + self.miss_penalty)
            ) / total

        stats = self.stats.copy()
        stats.update(
            {
                "cache_size": self.cache_size,
                "block_size": self.block_size,
                "associativity": self.associativity,
                "num_sets": self.num_sets,
                "replacement_policy": self.replacement_policy.value,  # type: ignore[dict-item]
                "write_policy": self.write_policy,  # type: ignore[dict-item]
                "current_cycle": self.current_cycle,
                "mshr_utilization": len(self.mshrs) / self.mshr_entries,
            }
        )

        return stats

    def reset_statistics(self) -> None:
        """Reset cache statistics."""
        self.stats = {
            "total_accesses": 0,
            "hits": 0,
            "misses": 0,
            "writebacks": 0,
            "mshr_hits": 0,
            "mshr_misses": 0,
            "average_access_time": 0.0,
            "hit_rate": 0.0,
            "miss_rate": 0.0,
            "cycles_stalled": 0,
        }


class MemoryHierarchy:
    """
    Complete memory hierarchy with multiple cache levels.
    """

    def __init__(
        self, l1_config: dict, l2_config: dict | None = None, memory_latency: int = 100
    ):
        """
        Initialize memory hierarchy.

        Args:
            l1_config: L1 cache configuration
            l2_config: L2 cache configuration (optional)
            memory_latency: Main memory access latency
        """
        self.l1_cache = EnhancedCache(**l1_config)
        self.l2_cache = EnhancedCache(**l2_config) if l2_config else None
        self.memory_latency = memory_latency

        self.stats = {
            "l1_accesses": 0,
            "l2_accesses": 0,
            "memory_accesses": 0,
            "total_cycles": 0,
        }

    def access(
        self, address: int, access_type: MemoryAccessType, data: int | None = None
    ) -> tuple[bool, int, int | None]:
        """
        Access memory hierarchy.

        Returns:
            (success, total_cycles, data) tuple
        """
        total_cycles = 0

        # Try L1 cache
        self.stats["l1_accesses"] += 1
        hit, cycles, result_data = self.l1_cache.access(address, access_type, data)
        total_cycles += cycles

        if hit:
            return True, total_cycles, result_data

        # L1 miss, try L2 if available
        if self.l2_cache:
            self.stats["l2_accesses"] += 1
            hit, cycles, result_data = self.l2_cache.access(address, access_type, data)
            total_cycles += cycles

            if hit:
                # Install in L1
                self.l1_cache.access(address, MemoryAccessType.READ, result_data)
                return True, total_cycles, result_data

        # Memory access required
        self.stats["memory_accesses"] += 1
        total_cycles += self.memory_latency

        # Simulate memory access (simplified)
        if access_type == MemoryAccessType.READ:
            result_data = 0  # Simplified
        else:
            result_data = data

        # Install in caches
        if self.l2_cache:
            self.l2_cache.access(address, MemoryAccessType.READ, result_data)
        self.l1_cache.access(address, MemoryAccessType.READ, result_data)

        return True, total_cycles, result_data

    def advance_cycle(self) -> None:
        """Advance all cache levels by one cycle."""
        self.l1_cache.advance_cycle()
        if self.l2_cache:
            self.l2_cache.advance_cycle()
        self.stats["total_cycles"] += 1

    def get_statistics(self) -> dict[str, Any]:
        """Get complete hierarchy statistics."""
        stats = self.stats.copy()
        stats["l1_stats"] = self.l1_cache.get_statistics()  # type: ignore[assignment]
        if self.l2_cache:
            stats["l2_stats"] = self.l2_cache.get_statistics()  # type: ignore[assignment]
        return stats
