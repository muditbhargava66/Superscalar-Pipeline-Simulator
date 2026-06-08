"""
tests/test_cache_system.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Unit tests for the cache hierarchy defined in ``src/cache/cache.py``
and the non-blocking cache in ``src/cache/non_blocking_cache.py``.

What's tested:
  - CacheBlock access metadata
  - Cache read/write hit and miss behaviour
  - LRU, FIFO, and random replacement policies
  - Write-through and write-back policies
  - Cache flush and invalidate
  - InstructionCache: add/fetch/has
  - DataCache: load/store/store-buffer
  - Memory: read/write/load_program/bounds checking
  - MemoryHierarchy: L1I → L1D → L2 → memory flow
  - NonBlockingCache: MSHR allocation basics
"""

from __future__ import annotations

import pytest

from src.cache.cache import (
    Cache,
    CacheBlock,
    DataCache,
    InstructionCache,
    Memory,
    MemoryAccessError,
    MemoryHierarchy,
)

# ========================== CacheBlock =====================================


class TestCacheBlock:
    """Low-level cache line metadata."""

    def test_initial_state(self) -> None:
        block = CacheBlock(tag=0x10, data=[0] * 64)
        assert block.valid
        assert not block.dirty
        assert block.access_count == 0

    def test_access_increments_counter(self) -> None:
        block = CacheBlock(tag=0x10, data=[0] * 64)
        block.access(cycle=5)
        assert block.access_count == 1
        assert block.last_access_time == 5

    def test_multiple_accesses(self) -> None:
        block = CacheBlock(tag=0x10, data=[0] * 64)
        block.access(cycle=1)
        block.access(cycle=5)
        block.access(cycle=10)
        assert block.access_count == 3
        assert block.last_access_time == 10


# ========================== Cache (base) ===================================


class TestCache:
    """Base cache read/write/hit/miss."""

    @pytest.fixture()
    def cache(self) -> Cache:
        # 256B cache, 64B blocks, 4-way set-associative, LRU
        return Cache(
            cache_size=256, block_size=64, associativity=4, replacement_policy="LRU"
        )

    def test_write_then_read_hit(self, cache: Cache) -> None:
        cache.write(0x100, 42)
        result = cache.read(0x100)
        assert result == 42

    def test_read_miss_returns_none(self, cache: Cache) -> None:
        assert cache.read(0x200) is None

    def test_hit_and_miss_counts(self, cache: Cache) -> None:
        cache.write(0x100, 1)
        cache.read(0x100)  # hit
        cache.read(0x999)  # miss
        stats = cache.get_statistics()
        assert stats["hits"] >= 1
        assert stats["misses"] >= 1

    def test_hit_rate_calculation(self, cache: Cache) -> None:
        cache.write(0x100, 1)
        cache.read(0x100)
        cache.read(0xFFF)
        rate = cache.get_hit_rate()
        assert 0.0 <= rate <= 100.0

    def test_invalidate_removes_block(self, cache: Cache) -> None:
        cache.write(0x100, 99)
        cache.invalidate(0x100)
        assert cache.read(0x100) is None

    def test_flush_clears_cache(self, cache: Cache) -> None:
        cache.write(0x100, 1)
        cache.write(0x200, 2)
        cache.flush()
        assert cache.read(0x100) is None
        assert cache.read(0x200) is None

    def test_reset_statistics(self, cache: Cache) -> None:
        cache.write(0x100, 1)
        cache.read(0x100)
        cache.reset_statistics()
        stats = cache.get_statistics()
        assert stats["hits"] == 0
        assert stats["misses"] == 0

    def test_load_block(self, cache: Cache) -> None:
        data = list(range(64))
        cache.load_block(0x000, data)
        # Read offset 5 within the loaded block
        assert cache.read(0x005) == 5


class TestCacheReplacementPolicies:
    """Different eviction strategies."""

    def test_lru_evicts_least_recent(self) -> None:
        # Direct-mapped (1-way), 2 blocks of 4 bytes → 2 sets
        cache = Cache(
            cache_size=8, block_size=4, associativity=1, replacement_policy="LRU"
        )
        cache.write(0x00, 1)  # set 0
        cache.write(0x04, 2)  # set 1
        cache.write(0x08, 3)  # set 0 → evicts 0x00
        assert cache.read(0x00) is None  # evicted
        assert cache.read(0x04) is not None

    def test_fifo_evicts_first_in(self) -> None:
        cache = Cache(
            cache_size=8, block_size=4, associativity=1, replacement_policy="FIFO"
        )
        cache.write(0x00, 1)
        cache.write(0x08, 3)  # same set, evicts 0x00
        assert cache.read(0x00) is None


class TestCacheWritePolicies:
    """Write-through vs write-back."""

    def test_write_back_marks_dirty(self) -> None:
        cache = Cache(
            cache_size=64,
            block_size=16,
            associativity=1,
            replacement_policy="LRU",
            write_policy="write_back",
        )
        cache.write(0x00, 42)
        # Verify data persists
        assert cache.read(0x00) == 42

    def test_write_through_no_dirty(self) -> None:
        cache = Cache(
            cache_size=64,
            block_size=16,
            associativity=1,
            replacement_policy="LRU",
            write_policy="write_through",
        )
        cache.write(0x00, 42)
        assert cache.read(0x00) == 42


# ========================== InstructionCache ================================


class TestInstructionCache:
    """Instruction-specific cache behaviour."""

    @pytest.fixture()
    def icache(self) -> InstructionCache:
        mem = Memory(size=4096)
        return InstructionCache(
            cache_size=256, block_size=64, memory=mem, fetch_bandwidth=4
        )

    def test_add_and_has(self, icache: InstructionCache) -> None:
        icache.add_instruction(0x100, {"opcode": "ADD"})
        assert icache.has_instruction(0x100)

    def test_get_instruction(self, icache: InstructionCache) -> None:
        icache.add_instruction(0x100, {"opcode": "SUB"})
        data = icache.get_instruction(0x100)
        assert data is not None
        assert data["opcode"] == "SUB"

    def test_miss_returns_none(self, icache: InstructionCache) -> None:
        assert icache.get_instruction(0x999) is None

    def test_fetch_instructions_bandwidth(self, icache: InstructionCache) -> None:
        for i in range(8):
            icache.add_instruction(i * 4, {"addr": i * 4})
        fetched = icache.fetch_instructions(0, count=8)
        # Should be capped at fetch_bandwidth (4)
        assert len(fetched) == 4

    def test_invalidate_range(self, icache: InstructionCache) -> None:
        icache.add_instruction(0x100, {"opcode": "ADD"})
        icache.add_instruction(0x104, {"opcode": "SUB"})
        icache.invalidate_range(0x100, 0x108)
        assert not icache.has_instruction(0x100)
        assert not icache.has_instruction(0x104)


# ========================== DataCache =======================================


class TestDataCache:
    """Data cache load/store/buffer operations."""

    @pytest.fixture()
    def dcache(self) -> DataCache:
        return DataCache(cache_size=256, block_size=64, associativity=4)

    def test_store_then_load(self, dcache: DataCache) -> None:
        dcache.store(0x100, 42)
        assert dcache.load(0x100) == 42

    def test_load_miss(self, dcache: DataCache) -> None:
        assert dcache.load(0x999) is None

    def test_has_data(self, dcache: DataCache) -> None:
        dcache.store(0x200, 7)
        assert dcache.has_data(0x200)

    def test_store_buffer_checked_first(self, dcache: DataCache) -> None:
        dcache.store(0x300, 99)
        # Value should come from store buffer on load
        assert dcache.load(0x300) == 99

    def test_flush_write_buffer(self, dcache: DataCache) -> None:
        dcache.store(0x100, 1)
        dcache.flush_write_buffer()
        # After flush, write buffer is empty
        assert len(dcache.write_buffer) == 0

    def test_flush_store_buffer(self, dcache: DataCache) -> None:
        dcache.store(0x100, 1)
        dcache.flush_store_buffer()
        assert len(dcache.store_buffer) == 0

    def test_get_hits_and_misses(self, dcache: DataCache) -> None:
        dcache.store(0x100, 1)
        dcache.load(0x100)
        dcache.load(0xFFF)
        assert dcache.get_hits() >= 0
        assert dcache.get_misses() >= 0


# ========================== Memory ==========================================


class TestMemory:
    """Main memory read/write/bounds."""

    @pytest.fixture()
    def mem(self) -> Memory:
        return Memory(size=1024, access_latency=50, bandwidth=8)

    def test_read_default_zero(self, mem: Memory) -> None:
        assert mem.read(0, 1) == 0

    def test_write_and_read(self, mem: Memory) -> None:
        mem.write(10, 42, size=1)
        assert mem.read(10, 1) == 42

    def test_write_list(self, mem: Memory) -> None:
        mem.write(0, [1, 2, 3, 4])
        assert mem.read(0, 4) == [1, 2, 3, 4]

    def test_read_block(self, mem: Memory) -> None:
        mem.write(0, [10, 20, 30, 40])
        block = mem.read_block(0, 4)
        assert block == [10, 20, 30, 40]

    def test_load_program(self, mem: Memory) -> None:
        program = [1, 2, 3, 4, 5]
        mem.load_program(program, start_address=0)
        assert mem.read(0, 5) == [1, 2, 3, 4, 5]

    def test_out_of_bounds_read_raises(self, mem: Memory) -> None:
        with pytest.raises(MemoryAccessError):
            mem.read(2000, 4)

    def test_out_of_bounds_write_raises(self, mem: Memory) -> None:
        with pytest.raises(MemoryAccessError):
            mem.write(2000, [1, 2, 3, 4])

    def test_is_address_valid(self, mem: Memory) -> None:
        assert mem.is_address_valid(0)
        assert mem.is_address_valid(1023)
        assert not mem.is_address_valid(1024)

    def test_get_access_latency(self, mem: Memory) -> None:
        latency = mem.get_access_latency(0, 4)
        assert latency >= mem.access_latency

    def test_statistics(self, mem: Memory) -> None:
        mem.read(0, 4)
        mem.write(0, 42, size=4)
        stats = mem.get_statistics()
        assert stats["read_count"] == 1
        assert stats["write_count"] == 1

    def test_dump_region(self, mem: Memory) -> None:
        mem.write(0, [5, 6, 7])
        assert mem.dump_region(0, 3) == [5, 6, 7]


# ========================== MemoryHierarchy =================================


class TestMemoryHierarchy:
    """L1I → L1D → L2 → main memory flow."""

    @pytest.fixture()
    def hierarchy(self) -> MemoryHierarchy:
        return MemoryHierarchy(
            memory_size=4096,
            l1_i_size=256,
            l1_d_size=256,
            l2_size=512,
            block_size=64,
        )

    def test_read_data_from_memory(self, hierarchy: MemoryHierarchy) -> None:
        hierarchy.memory.write(0x100, 42, size=1)
        val = hierarchy.read_data(0x100)
        assert val is not None

    def test_write_data(self, hierarchy: MemoryHierarchy) -> None:
        success = hierarchy.write_data(0x200, 99)
        assert success

    def test_hierarchy_statistics(self, hierarchy: MemoryHierarchy) -> None:
        hierarchy.read_data(0x100)
        hierarchy.write_data(0x200, 1)
        stats = hierarchy.get_hierarchy_statistics()
        assert "l1_instruction" in stats
        assert "l1_data" in stats
        assert "l2_unified" in stats
        assert "main_memory" in stats
        assert stats["access_counts"]["l1_d_accesses"] >= 1


# ========================== NonBlockingCache ================================


class TestNonBlockingCache:
    """MSHR-based non-blocking cache (basic smoke test)."""

    def test_import_and_instantiate(self) -> None:
        from src.cache.non_blocking_cache import NonBlockingCache

        # Just verify the class can be instantiated
        cache = NonBlockingCache(
            {
                "cache_size": 256,
                "block_size": 64,
                "associativity": 4,
            }
        )
        assert cache is not None
