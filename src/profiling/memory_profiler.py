"""
Memory profiling tools for the simulator.

This module provides detailed memory usage analysis including
memory leaks detection, allocation patterns, and memory optimization
recommendations.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import gc
import tracemalloc
from typing import Any, Optional

import psutil


@dataclass
class MemorySnapshot:
    """Snapshot of memory usage at a specific point in time."""
    
    timestamp: float
    rss_memory: float  # Resident Set Size in MB
    vms_memory: float  # Virtual Memory Size in MB
    python_memory: float  # Python-specific memory in MB
    gc_stats: dict[str, int]
    top_allocations: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class MemoryProfileResult:
    """Results from memory profiling analysis."""
    
    initial_snapshot: MemorySnapshot
    final_snapshot: MemorySnapshot
    peak_memory: float
    memory_growth: float
    potential_leaks: list[dict[str, Any]] = field(default_factory=list)
    allocation_patterns: dict[str, Any] = field(default_factory=dict)
    recommendations: list[str] = field(default_factory=list)


class MemoryProfiler:
    """
    Advanced memory profiler for the simulator.
    
    Tracks memory usage patterns, identifies potential leaks,
    and provides optimization recommendations.
    """
    
    def __init__(self, track_allocations: bool = True):
        """
        Initialize memory profiler.
        
        Args:
            track_allocations: Enable detailed allocation tracking
        """
        self.track_allocations = track_allocations
        self._process = psutil.Process()
        self._initial_snapshot: Optional[MemorySnapshot] = None
        self._snapshots: list[MemorySnapshot] = []
        self._tracemalloc_started = False
    
    def start_profiling(self) -> None:
        """Start memory profiling."""
        if self.track_allocations:
            tracemalloc.start()
            self._tracemalloc_started = True
        
        self._initial_snapshot = self._take_snapshot()
        self._snapshots = [self._initial_snapshot]
    
    def take_snapshot(self) -> MemorySnapshot:
        """Take a memory snapshot at current point."""
        snapshot = self._take_snapshot()
        self._snapshots.append(snapshot)
        return snapshot
    
    def stop_profiling(self) -> MemoryProfileResult:
        """
        Stop memory profiling and return analysis results.
        
        Returns:
            Comprehensive memory profiling results
        """
        if self._initial_snapshot is None:
            raise RuntimeError("Memory profiling not started")
        
        final_snapshot = self._take_snapshot()
        self._snapshots.append(final_snapshot)
        
        if self._tracemalloc_started:
            tracemalloc.stop()
            self._tracemalloc_started = False
        
        # Analyze results
        result = self._analyze_memory_usage(self._initial_snapshot, final_snapshot)
        
        return result
    
    def _take_snapshot(self) -> MemorySnapshot:
        """Take a detailed memory snapshot."""
        import time
        
        # Get system memory info
        memory_info = self._process.memory_info()
        
        # Get Python-specific memory info
        python_memory = 0
        if self._tracemalloc_started:
            current, peak = tracemalloc.get_traced_memory()
            python_memory = current / 1024 / 1024  # Convert to MB
        
        # Get garbage collection stats
        gc_stats = {
            f'generation_{i}': len(gc.get_objects(i))
            for i in range(3)
        }
        gc_stats['total_objects'] = len(gc.get_objects())
        
        # Get top allocations if tracking is enabled
        top_allocations = []
        if self._tracemalloc_started:
            top_allocations = self._get_top_allocations()
        
        return MemorySnapshot(
            timestamp=time.time(),
            rss_memory=memory_info.rss / 1024 / 1024,  # MB
            vms_memory=memory_info.vms / 1024 / 1024,  # MB
            python_memory=python_memory,
            gc_stats=gc_stats,
            top_allocations=top_allocations,
        )
    
    def _get_top_allocations(self, limit: int = 10) -> list[dict[str, Any]]:
        """Get top memory allocations."""
        if not self._tracemalloc_started:
            return []
        
        snapshot = tracemalloc.take_snapshot()
        top_stats = snapshot.statistics('lineno')
        
        allocations = []
        for stat in top_stats[:limit]:
            allocations.append({
                'filename': stat.traceback.format()[0] if stat.traceback else 'unknown',
                'size_mb': stat.size / 1024 / 1024,
                'count': stat.count,
                'average_size': stat.size / stat.count if stat.count > 0 else 0,
            })
        
        return allocations
    
    def _analyze_memory_usage(self, initial: MemorySnapshot,
                            final: MemorySnapshot) -> MemoryProfileResult:
        """Analyze memory usage patterns and identify issues."""
        # Calculate basic metrics
        memory_growth = final.rss_memory - initial.rss_memory
        peak_memory = max(snapshot.rss_memory for snapshot in self._snapshots)
        
        # Identify potential leaks
        potential_leaks = self._identify_potential_leaks()
        
        # Analyze allocation patterns
        allocation_patterns = self._analyze_allocation_patterns()
        
        # Generate recommendations
        recommendations = self._generate_memory_recommendations(
            memory_growth, peak_memory, potential_leaks
        )
        
        return MemoryProfileResult(
            initial_snapshot=initial,
            final_snapshot=final,
            peak_memory=peak_memory,
            memory_growth=memory_growth,
            potential_leaks=potential_leaks,
            allocation_patterns=allocation_patterns,
            recommendations=recommendations,
        )
    
    def _identify_potential_leaks(self) -> list[dict[str, Any]]:
        """Identify potential memory leaks."""
        leaks = []
        
        if len(self._snapshots) < 2:
            return leaks
        
        # Check for consistent memory growth
        growth_rates = []
        for i in range(1, len(self._snapshots)):
            prev = self._snapshots[i-1]
            curr = self._snapshots[i]
            growth = curr.rss_memory - prev.rss_memory
            growth_rates.append(growth)
        
        # If memory consistently grows, it might indicate a leak
        if len(growth_rates) >= 3 and all(rate > 0 for rate in growth_rates[-3:]):
            avg_growth = sum(growth_rates[-3:]) / 3
            if avg_growth > 1:  # More than 1MB per snapshot
                leaks.append({
                    'type': 'consistent_growth',
                    'description': 'Memory consistently growing across snapshots',
                    'average_growth_mb': avg_growth,
                    'severity': 'high' if avg_growth > 5 else 'medium',
                })
        
        # Check for object count growth
        initial_objects = self._snapshots[0].gc_stats.get('total_objects', 0)
        final_objects = self._snapshots[-1].gc_stats.get('total_objects', 0)
        object_growth = final_objects - initial_objects
        
        if object_growth > 1000:  # More than 1000 new objects
            leaks.append({
                'type': 'object_growth',
                'description': 'Significant increase in Python object count',
                'object_growth': object_growth,
                'severity': 'medium',
            })
        
        return leaks
    
    def _analyze_allocation_patterns(self) -> dict[str, Any]:
        """Analyze memory allocation patterns."""
        patterns = {}
        
        if not self._snapshots:
            return patterns
        
        # Analyze allocation distribution
        if self._snapshots[-1].top_allocations:
            allocations = self._snapshots[-1].top_allocations
            
            total_size = sum(alloc['size_mb'] for alloc in allocations)
            patterns['top_allocators'] = allocations[:5]
            patterns['allocation_concentration'] = (
                allocations[0]['size_mb'] / total_size * 100
                if total_size > 0 else 0
            )
        
        # Analyze memory growth pattern
        if len(self._snapshots) > 1:
            memory_timeline = [s.rss_memory for s in self._snapshots]
            patterns['growth_pattern'] = {
                'initial': memory_timeline[0],
                'final': memory_timeline[-1],
                'peak': max(memory_timeline),
                'volatility': max(memory_timeline) - min(memory_timeline),
            }
        
        return patterns
    
    def _generate_memory_recommendations(self, memory_growth: float,
                                       peak_memory: float,
                                       potential_leaks: list[dict[str, Any]]) -> list[str]:
        """Generate memory optimization recommendations."""
        recommendations = []
        
        # Memory growth recommendations
        if memory_growth > 50:  # More than 50MB growth
            recommendations.append(
                "Consider implementing object pooling to reduce memory allocations"
            )
            recommendations.append(
                "Review data structures for memory efficiency"
            )
        
        # Peak memory recommendations
        if peak_memory > 500:  # More than 500MB peak
            recommendations.append(
                "Consider processing data in smaller chunks to reduce peak memory usage"
            )
        
        # Leak-specific recommendations
        for leak in potential_leaks:
            if leak['type'] == 'consistent_growth':
                recommendations.append(
                    "Investigate potential memory leaks - memory is consistently growing"
                )
            elif leak['type'] == 'object_growth':
                recommendations.append(
                    "Review object lifecycle management - many objects are not being freed"
                )
        
        # General recommendations
        if not recommendations:
            recommendations.append("Memory usage appears optimal")
        else:
            recommendations.append("Run garbage collection explicitly at key points")
            recommendations.append("Consider using __slots__ for frequently created objects")
        
        return recommendations
    
    def generate_memory_report(self, output_file: str) -> None:
        """
        Generate a detailed memory usage report.
        
        Args:
            output_file: Path to output report file
        """
        if not self._snapshots:
            raise RuntimeError("No memory snapshots available")
        
        result = self.stop_profiling() if self._initial_snapshot else None
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("Memory Profiling Report\n")
            f.write("=" * 50 + "\n\n")
            
            if result:
                f.write(f"Memory Growth: {result.memory_growth:.2f} MB\n")
                f.write(f"Peak Memory: {result.peak_memory:.2f} MB\n")
                f.write(f"Potential Leaks: {len(result.potential_leaks)}\n\n")
                
                if result.potential_leaks:
                    f.write("Potential Memory Leaks:\n")
                    for leak in result.potential_leaks:
                        f.write(f"  - {leak['description']} (Severity: {leak['severity']})\n")
                    f.write("\n")
                
                f.write("Recommendations:\n")
                for rec in result.recommendations:
                    f.write(f"  - {rec}\n")
            
            f.write("\nSnapshot Timeline:\n")
            for i, snapshot in enumerate(self._snapshots):
                f.write(f"  Snapshot {i}: {snapshot.rss_memory:.2f} MB RSS, "
                       f"{snapshot.python_memory:.2f} MB Python\n")
