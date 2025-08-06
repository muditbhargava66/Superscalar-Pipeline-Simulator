"""
Advanced performance profiling tools for the simulator.

This module provides comprehensive profiling capabilities including
execution time analysis, bottleneck identification, and performance
optimization recommendations.
"""

from __future__ import annotations

from contextlib import contextmanager
import cProfile
from dataclasses import dataclass, field
from pathlib import Path
import pstats
import time
from typing import Any, Optional

import psutil


@dataclass
class ProfileResult:
    """Results from a performance profiling session."""
    
    execution_time: float
    cpu_usage: dict[str, float]
    memory_usage: dict[str, float]
    function_stats: dict[str, Any]
    bottlenecks: list[dict[str, Any]] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert profile result to dictionary."""
        return {
            'execution_time': self.execution_time,
            'cpu_usage': self.cpu_usage,
            'memory_usage': self.memory_usage,
            'function_stats': self.function_stats,
            'bottlenecks': self.bottlenecks,
            'recommendations': self.recommendations,
        }


class PerformanceProfiler:
    """
    Advanced performance profiler for the simulator.
    
    Provides detailed analysis of execution time, CPU usage, memory consumption,
    and identifies performance bottlenecks.
    """
    
    def __init__(self, enable_detailed_profiling: bool = True):
        """
        Initialize the performance profiler.
        
        Args:
            enable_detailed_profiling: Enable detailed function-level profiling
        """
        self.enable_detailed_profiling = enable_detailed_profiling
        self._profiler: Optional[cProfile.Profile] = None
        self._start_time: Optional[float] = None
        self._process = psutil.Process()
        self._initial_cpu_times: Optional[psutil._common.pcputimes] = None
        self._initial_memory_info: Optional[psutil._common.pmem] = None
    
    @contextmanager
    def profile_simulation(self):
        """
        Context manager for profiling a simulation run.
        
        Usage:
            profiler = PerformanceProfiler()
            with profiler.profile_simulation() as session:
                # Run simulation
                result = simulator.run()
            
            profile_result = session.get_results()
        """
        session = ProfilingSession(self)
        session.start()
        try:
            yield session
        finally:
            session.stop()
    
    def start_profiling(self) -> None:
        """Start performance profiling."""
        if self.enable_detailed_profiling:
            self._profiler = cProfile.Profile()
            self._profiler.enable()
        
        self._start_time = time.time()
        self._initial_cpu_times = self._process.cpu_times()
        self._initial_memory_info = self._process.memory_info()
    
    def stop_profiling(self) -> ProfileResult:
        """
        Stop profiling and return results.
        
        Returns:
            Comprehensive profiling results
        """
        if self._start_time is None:
            raise RuntimeError("Profiling not started")
        
        execution_time = time.time() - self._start_time
        
        # Stop detailed profiling
        if self._profiler:
            self._profiler.disable()
        
        # Collect system metrics
        final_cpu_times = self._process.cpu_times()
        final_memory_info = self._process.memory_info()
        
        cpu_usage = self._calculate_cpu_usage(
            self._initial_cpu_times, final_cpu_times, execution_time
        )
        
        memory_usage = self._calculate_memory_usage(
            self._initial_memory_info, final_memory_info
        )
        
        # Analyze function performance
        function_stats = {}
        if self._profiler:
            function_stats = self._analyze_function_stats()
        
        # Create result
        result = ProfileResult(
            execution_time=execution_time,
            cpu_usage=cpu_usage,
            memory_usage=memory_usage,
            function_stats=function_stats,
        )
        
        # Analyze bottlenecks and generate recommendations
        analyzer = BottleneckAnalyzer(result)
        result.bottlenecks = analyzer.identify_bottlenecks()
        result.recommendations = analyzer.generate_recommendations()
        
        return result
    
    def _calculate_cpu_usage(self, initial: psutil._common.pcputimes,
                           final: psutil._common.pcputimes,
                           execution_time: float) -> dict[str, float]:
        """Calculate CPU usage statistics."""
        user_time = final.user - initial.user
        system_time = final.system - initial.system
        total_cpu_time = user_time + system_time
        
        return {
            'user_time': user_time,
            'system_time': system_time,
            'total_cpu_time': total_cpu_time,
            'cpu_utilization': (total_cpu_time / execution_time) * 100,
        }
    
    def _calculate_memory_usage(self, initial: psutil._common.pmem,
                              final: psutil._common.pmem) -> dict[str, float]:
        """Calculate memory usage statistics."""
        return {
            'initial_rss': initial.rss / 1024 / 1024,  # MB
            'final_rss': final.rss / 1024 / 1024,      # MB
            'peak_rss': final.rss / 1024 / 1024,       # MB (approximation)
            'memory_growth': (final.rss - initial.rss) / 1024 / 1024,  # MB
        }
    
    def _analyze_function_stats(self) -> dict[str, Any]:
        """Analyze function-level performance statistics."""
        if not self._profiler:
            return {}
        
        stats = pstats.Stats(self._profiler)
        stats.sort_stats('cumulative')
        
        # Extract top functions by various metrics
        function_stats = {
            'total_calls': stats.total_calls,
            'total_time': stats.total_tt,
            'top_by_cumulative': self._extract_top_functions(stats, 'cumulative', 10),
            'top_by_time': self._extract_top_functions(stats, 'time', 10),
            'top_by_calls': self._extract_top_functions(stats, 'calls', 10),
        }
        
        return function_stats
    
    def _extract_top_functions(self, stats: pstats.Stats,
                             sort_key: str, limit: int) -> list[dict[str, Any]]:
        """Extract top functions by specified metric."""
        stats.sort_stats(sort_key)
        
        top_functions = []
        for func_info, (cc, nc, tt, ct, callers) in list(stats.stats.items())[:limit]:
            filename, line_num, func_name = func_info
            
            top_functions.append({
                'function': func_name,
                'filename': filename,
                'line_number': line_num,
                'call_count': cc,
                'total_time': tt,
                'cumulative_time': ct,
                'time_per_call': tt / cc if cc > 0 else 0,
            })
        
        return top_functions
    
    def save_profile_data(self, output_file: str | Path) -> None:
        """
        Save detailed profiling data to file.
        
        Args:
            output_file: Output file path
        """
        if not self._profiler:
            raise RuntimeError("No profiling data available")
        
        self._profiler.dump_stats(str(output_file))


class ProfilingSession:
    """Represents an active profiling session."""
    
    def __init__(self, profiler: PerformanceProfiler):
        """Initialize profiling session."""
        self.profiler = profiler
        self._result: Optional[ProfileResult] = None
    
    def start(self) -> None:
        """Start the profiling session."""
        self.profiler.start_profiling()
    
    def stop(self) -> None:
        """Stop the profiling session."""
        self._result = self.profiler.stop_profiling()
    
    def get_results(self) -> ProfileResult:
        """Get profiling results."""
        if self._result is None:
            raise RuntimeError("Profiling session not completed")
        return self._result


class BottleneckAnalyzer:
    """Analyzes profiling results to identify performance bottlenecks."""
    
    def __init__(self, profile_result: ProfileResult):
        """
        Initialize bottleneck analyzer.
        
        Args:
            profile_result: Results from performance profiling
        """
        self.profile_result = profile_result
    
    def identify_bottlenecks(self) -> list[dict[str, Any]]:
        """
        Identify performance bottlenecks from profiling data.
        
        Returns:
            List of identified bottlenecks with details
        """
        bottlenecks = []
        
        # Analyze CPU usage
        cpu_bottlenecks = self._analyze_cpu_bottlenecks()
        bottlenecks.extend(cpu_bottlenecks)
        
        # Analyze memory usage
        memory_bottlenecks = self._analyze_memory_bottlenecks()
        bottlenecks.extend(memory_bottlenecks)
        
        # Analyze function performance
        function_bottlenecks = self._analyze_function_bottlenecks()
        bottlenecks.extend(function_bottlenecks)
        
        return bottlenecks
    
    def _analyze_cpu_bottlenecks(self) -> list[dict[str, Any]]:
        """Analyze CPU-related bottlenecks."""
        bottlenecks = []
        cpu_usage = self.profile_result.cpu_usage
        
        if cpu_usage.get('cpu_utilization', 0) > 90:
            bottlenecks.append({
                'type': 'cpu_intensive',
                'severity': 'high',
                'description': 'High CPU utilization detected',
                'value': cpu_usage['cpu_utilization'],
                'threshold': 90,
            })
        
        return bottlenecks
    
    def _analyze_memory_bottlenecks(self) -> list[dict[str, Any]]:
        """Analyze memory-related bottlenecks."""
        bottlenecks = []
        memory_usage = self.profile_result.memory_usage
        
        memory_growth = memory_usage.get('memory_growth', 0)
        if memory_growth > 100:  # More than 100MB growth
            bottlenecks.append({
                'type': 'memory_growth',
                'severity': 'medium',
                'description': 'Significant memory growth detected',
                'value': memory_growth,
                'threshold': 100,
            })
        
        return bottlenecks
    
    def _analyze_function_bottlenecks(self) -> list[dict[str, Any]]:
        """Analyze function-level bottlenecks."""
        bottlenecks = []
        function_stats = self.profile_result.function_stats
        
        if 'top_by_cumulative' in function_stats:
            top_functions = function_stats['top_by_cumulative']
            
            for func in top_functions[:3]:  # Top 3 functions
                if func['cumulative_time'] > 0.1:  # More than 100ms
                    bottlenecks.append({
                        'type': 'slow_function',
                        'severity': 'medium',
                        'description': f"Function '{func['function']}' consuming significant time",
                        'function': func['function'],
                        'cumulative_time': func['cumulative_time'],
                        'call_count': func['call_count'],
                    })
        
        return bottlenecks
    
    def generate_recommendations(self) -> list[str]:
        """
        Generate performance optimization recommendations.
        
        Returns:
            List of optimization recommendations
        """
        recommendations = []
        
        for bottleneck in self.profile_result.bottlenecks:
            if bottleneck['type'] == 'cpu_intensive':
                recommendations.append(
                    "Consider optimizing CPU-intensive operations or using parallel processing"
                )
            elif bottleneck['type'] == 'memory_growth':
                recommendations.append(
                    "Review memory usage patterns and consider implementing memory pooling"
                )
            elif bottleneck['type'] == 'slow_function':
                func_name = bottleneck.get('function', 'unknown')
                recommendations.append(
                    f"Optimize function '{func_name}' which is consuming significant execution time"
                )
        
        # General recommendations based on execution time
        if self.profile_result.execution_time > 10:
            recommendations.append(
                "Consider reducing simulation complexity or implementing caching"
            )
        
        return recommendations
