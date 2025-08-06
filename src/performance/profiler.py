"""
Performance Profiler Module

This module provides comprehensive performance profiling and analysis tools
for the superscalar pipeline simulator.

Author: Mudit Bhargava
Date: August2025
Python Version: 3.10+
"""

from __future__ import annotations

from collections import defaultdict, deque
import csv
from dataclasses import dataclass, field
import json
from pathlib import Path
import time
from typing import Any


@dataclass
class PerformanceMetrics:
    """Container for various performance metrics."""

    # Basic metrics
    total_cycles: int = 0
    total_instructions: int = 0
    ipc: float = 0.0

    # Branch metrics
    branch_predictions: int = 0
    branch_mispredictions: int = 0
    branch_accuracy: float = 0.0
    branch_penalty_cycles: int = 0

    # Cache metrics
    icache_hits: int = 0
    icache_misses: int = 0
    icache_hit_rate: float = 0.0
    dcache_hits: int = 0
    dcache_misses: int = 0
    dcache_hit_rate: float = 0.0
    cache_miss_penalty_cycles: int = 0

    # Stall metrics
    data_stalls: int = 0
    structural_stalls: int = 0
    control_stalls: int = 0
    total_stalls: int = 0

    # Hazard metrics
    raw_hazards: int = 0
    war_hazards: int = 0
    waw_hazards: int = 0

    # Functional unit metrics
    alu_utilization: float = 0.0
    fpu_utilization: float = 0.0
    lsu_utilization: float = 0.0

    # Instruction mix
    arithmetic_instructions: int = 0
    logical_instructions: int = 0
    memory_instructions: int = 0
    branch_instructions: int = 0
    floating_point_instructions: int = 0

    def calculate_derived_metrics(self) -> None:
        """Calculate derived metrics from raw counts."""
        # IPC
        if self.total_cycles > 0:
            self.ipc = self.total_instructions / self.total_cycles

        # Branch accuracy
        if self.branch_predictions > 0:
            self.branch_accuracy = ((self.branch_predictions - self.branch_mispredictions)
                                   / self.branch_predictions * 100)

        # Cache hit rates
        if self.icache_hits + self.icache_misses > 0:
            self.icache_hit_rate = self.icache_hits / (self.icache_hits + self.icache_misses) * 100

        if self.dcache_hits + self.dcache_misses > 0:
            self.dcache_hit_rate = self.dcache_hits / (self.dcache_hits + self.dcache_misses) * 100

        # Total stalls
        self.total_stalls = self.data_stalls + self.structural_stalls + self.control_stalls


@dataclass
class CycleSnapshot:
    """Detailed information about a single cycle."""
    cycle: int
    fetched_instructions: List[str] = field(default_factory=list)
    decoded_instructions: List[str] = field(default_factory=list)
    issued_instructions: List[str] = field(default_factory=list)
    executed_instructions: List[str] = field(default_factory=list)
    memory_instructions: List[str] = field(default_factory=list)
    writeback_instructions: List[str] = field(default_factory=list)
    stalls: Dict[str, int] = field(default_factory=dict)
    hazards: List[str] = field(default_factory=list)
    branch_predictions: List[Tuple[str, bool]] = field(default_factory=list)
    cache_accesses: List[Tuple[str, bool]] = field(default_factory=list)


class PerformanceProfiler:
    """
    Comprehensive performance profiler for the pipeline simulator.
    
    Tracks detailed metrics, identifies bottlenecks, and provides
    analysis and recommendations.
    """

    def __init__(self, enable_detailed_tracking: bool = False) -> None:
        """
        Initialize the performance profiler.
        
        Args:
            enable_detailed_tracking: Whether to track per-cycle details
        """
        self.metrics = PerformanceMetrics()
        self.enable_detailed_tracking = enable_detailed_tracking

        # Cycle-by-cycle tracking
        self.cycle_snapshots: List[CycleSnapshot] = []
        self.current_cycle = 0

        # Time series data
        self.ipc_history: deque = deque(maxlen=1000)
        self.branch_accuracy_history: deque = deque(maxlen=1000)
        self.cache_hit_history: deque = deque(maxlen=1000)

        # Instruction tracking
        self.instruction_latencies: Dict[str, List[int]] = defaultdict(list)
        self.instruction_counts: Dict[str, int] = defaultdict(int)

        # Bottleneck analysis
        self.bottleneck_events: List[Dict] = []
        self.critical_path_instructions: List[str] = []

        # Real-time performance
        self.start_time = time.time()
        self.simulation_time = 0.0

    def start_cycle(self, cycle: int) -> None:
        """Begin tracking a new cycle."""
        self.current_cycle = cycle
        if self.enable_detailed_tracking:
            self.cycle_snapshots.append(CycleSnapshot(cycle))

    def end_cycle(self) -> None:
        """Finalize tracking for the current cycle."""
        self.metrics.total_cycles += 1

        # Update time series
        if self.metrics.total_cycles > 0:
            current_ipc = self.metrics.total_instructions / self.metrics.total_cycles
            self.ipc_history.append(current_ipc)

    def record_instruction_fetch(self, instructions: List[str]) -> None:
        """Record fetched instructions."""
        if self.enable_detailed_tracking and self.cycle_snapshots:
            self.cycle_snapshots[-1].fetched_instructions.extend(instructions)

    def record_instruction_complete(self, instruction: str,
                                  issue_cycle: int, complete_cycle: int) -> None:
        """Record instruction completion with latency."""
        self.metrics.total_instructions += 1

        # Track latency
        latency = complete_cycle - issue_cycle
        self.instruction_latencies[instruction].append(latency)
        self.instruction_counts[instruction] += 1

        # Update instruction mix
        self._update_instruction_mix(instruction)

    def _update_instruction_mix(self, instruction: str) -> None:
        """Update instruction type counters."""
        opcode = instruction.split()[0].upper() if instruction else ""

        if opcode in ["ADD", "SUB", "MUL", "DIV", "ADDI", "SUBI"]:
            self.metrics.arithmetic_instructions += 1
        elif opcode in ["AND", "OR", "XOR", "SLT", "ANDI", "ORI", "XORI", "SLTI"]:
            self.metrics.logical_instructions += 1
        elif opcode in ["LW", "SW", "LB", "LH", "SB", "SH"]:
            self.metrics.memory_instructions += 1
        elif opcode in ["BEQ", "BNE", "BLT", "BGE", "J", "JAL", "JR", "JALR"]:
            self.metrics.branch_instructions += 1
        elif opcode in ["FADD", "FSUB", "FMUL", "FDIV"]:
            self.metrics.floating_point_instructions += 1

    def record_branch_prediction(self, instruction: str,
                               predicted: bool, actual: bool) -> None:
        """Record branch prediction outcome."""
        self.metrics.branch_predictions += 1
        if predicted != actual:
            self.metrics.branch_mispredictions += 1
            self.metrics.branch_penalty_cycles += 3  # Typical penalty

        if self.enable_detailed_tracking and self.cycle_snapshots:
            self.cycle_snapshots[-1].branch_predictions.append(
                (instruction, predicted == actual)
            )

        # Update history
        if self.metrics.branch_predictions > 0:
            accuracy = ((self.metrics.branch_predictions - self.metrics.branch_mispredictions)
                       / self.metrics.branch_predictions * 100)
            self.branch_accuracy_history.append(accuracy)

    def record_cache_access(self, cache_type: str, hit: bool,
                           miss_penalty: int = 10) -> None:
        """Record cache access."""
        if cache_type == "instruction":
            if hit:
                self.metrics.icache_hits += 1
            else:
                self.metrics.icache_misses += 1
                self.metrics.cache_miss_penalty_cycles += miss_penalty
        elif hit:
            self.metrics.dcache_hits += 1
        else:
            self.metrics.dcache_misses += 1
            self.metrics.cache_miss_penalty_cycles += miss_penalty

        if self.enable_detailed_tracking and self.cycle_snapshots:
            self.cycle_snapshots[-1].cache_accesses.append((cache_type, hit))

    def record_stall(self, stall_type: str, duration: int = 1) -> None:
        """Record pipeline stall."""
        if stall_type == "data":
            self.metrics.data_stalls += duration
        elif stall_type == "structural":
            self.metrics.structural_stalls += duration
        elif stall_type == "control":
            self.metrics.control_stalls += duration

        if self.enable_detailed_tracking and self.cycle_snapshots:
            if stall_type not in self.cycle_snapshots[-1].stalls:
                self.cycle_snapshots[-1].stalls[stall_type] = 0
            self.cycle_snapshots[-1].stalls[stall_type] += duration

    def record_hazard(self, hazard_type: str, description: str = "") -> None:
        """Record pipeline hazard."""
        if hazard_type == "RAW":
            self.metrics.raw_hazards += 1
        elif hazard_type == "WAR":
            self.metrics.war_hazards += 1
        elif hazard_type == "WAW":
            self.metrics.waw_hazards += 1

        if self.enable_detailed_tracking and self.cycle_snapshots:
            self.cycle_snapshots[-1].hazards.append(f"{hazard_type}: {description}")

    def record_functional_unit_usage(self, unit_type: str,
                                   busy_cycles: int, total_cycles: int) -> None:
        """Record functional unit utilization."""
        if total_cycles == 0:
            return

        utilization = (busy_cycles / total_cycles) * 100

        if unit_type == "ALU":
            self.metrics.alu_utilization = utilization
        elif unit_type == "FPU":
            self.metrics.fpu_utilization = utilization
        elif unit_type == "LSU":
            self.metrics.lsu_utilization = utilization

    def identify_bottleneck(self, description: str, severity: str = "medium") -> None:
        """Record a performance bottleneck."""
        self.bottleneck_events.append({
            'cycle': self.current_cycle,
            'description': description,
            'severity': severity,
            'metrics_snapshot': {
                'ipc': self.metrics.ipc,
                'stalls': self.metrics.total_stalls,
                'branch_accuracy': self.metrics.branch_accuracy
            }
        })

    def analyze_critical_path(self) -> List[str]:
        """Identify instructions on the critical execution path."""
        # Find instructions with highest latencies
        critical_instructions = []

        for instruction, latencies in self.instruction_latencies.items():
            if latencies:
                avg_latency = sum(latencies) / len(latencies)
                max_latency = max(latencies)

                if max_latency > 10:  # Threshold for critical
                    critical_instructions.append({
                        'instruction': instruction,
                        'avg_latency': avg_latency,
                        'max_latency': max_latency,
                        'count': len(latencies)
                    })

        # Sort by impact (latency * count)
        critical_instructions.sort(
            key=lambda x: x['max_latency'] * x['count'],
            reverse=True
        )

        self.critical_path_instructions = [
            inst['instruction'] for inst in critical_instructions[:10]
        ]

        return self.critical_path_instructions

    def get_performance_summary(self) -> Dict[str, Any]:
        """Generate comprehensive performance summary."""
        self.metrics.calculate_derived_metrics()

        # Additional statistics could be calculated here if needed

        # Identify top bottlenecks
        bottleneck_summary = defaultdict(int)
        for event in self.bottleneck_events:
            bottleneck_summary[event['description']] += 1

        top_bottlenecks = sorted(
            bottleneck_summary.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]

        return {
            'basic_metrics': {
                'total_cycles': self.metrics.total_cycles,
                'total_instructions': self.metrics.total_instructions,
                'ipc': round(self.metrics.ipc, 3),
                'simulation_time': time.time() - self.start_time
            },
            'branch_performance': {
                'predictions': self.metrics.branch_predictions,
                'mispredictions': self.metrics.branch_mispredictions,
                'accuracy': round(self.metrics.branch_accuracy, 2),
                'penalty_cycles': self.metrics.branch_penalty_cycles
            },
            'cache_performance': {
                'icache_hit_rate': round(self.metrics.icache_hit_rate, 2),
                'dcache_hit_rate': round(self.metrics.dcache_hit_rate, 2),
                'total_miss_penalty': self.metrics.cache_miss_penalty_cycles
            },
            'stall_analysis': {
                'data_stalls': self.metrics.data_stalls,
                'structural_stalls': self.metrics.structural_stalls,
                'control_stalls': self.metrics.control_stalls,
                'total_stalls': self.metrics.total_stalls,
                'stall_percentage': round(
                    self.metrics.total_stalls / self.metrics.total_cycles * 100
                    if self.metrics.total_cycles > 0 else 0, 2
                )
            },
            'hazard_analysis': {
                'raw_hazards': self.metrics.raw_hazards,
                'war_hazards': self.metrics.war_hazards,
                'waw_hazards': self.metrics.waw_hazards
            },
            'functional_unit_utilization': {
                'alu': round(self.metrics.alu_utilization, 2),
                'fpu': round(self.metrics.fpu_utilization, 2),
                'lsu': round(self.metrics.lsu_utilization, 2)
            },
            'instruction_mix': {
                'arithmetic': self.metrics.arithmetic_instructions,
                'logical': self.metrics.logical_instructions,
                'memory': self.metrics.memory_instructions,
                'branch': self.metrics.branch_instructions,
                'floating_point': self.metrics.floating_point_instructions
            },
            'bottlenecks': top_bottlenecks,
            'critical_path': self.critical_path_instructions[:5]
        }

    def generate_recommendations(self) -> List[str]:
        """Generate performance improvement recommendations."""
        recommendations = []

        # Branch prediction
        if self.metrics.branch_accuracy < 85:
            recommendations.append(
                f"Branch prediction accuracy is {self.metrics.branch_accuracy:.1f}%. "
                "Consider using a more sophisticated predictor (e.g., tournament or TAGE)."
            )

        # Cache performance
        if self.metrics.icache_hit_rate < 95:
            recommendations.append(
                f"Instruction cache hit rate is {self.metrics.icache_hit_rate:.1f}%. "
                "Consider increasing cache size or improving code locality."
            )

        if self.metrics.dcache_hit_rate < 90:
            recommendations.append(
                f"Data cache hit rate is {self.metrics.dcache_hit_rate:.1f}%. "
                "Consider data prefetching or cache-conscious data structures."
            )

        # Stalls
        stall_percentage = (self.metrics.total_stalls / self.metrics.total_cycles * 100
                           if self.metrics.total_cycles > 0 else 0)
        if stall_percentage > 20:
            recommendations.append(
                f"Pipeline stalls account for {stall_percentage:.1f}% of cycles. "
                "Focus on reducing data dependencies and improving scheduling."
            )

        # Functional unit utilization
        if self.metrics.alu_utilization < 50:
            recommendations.append(
                "ALU utilization is low. Consider increasing issue width or "
                "improving instruction-level parallelism."
            )

        # IPC
        if self.metrics.ipc < 2.0:
            recommendations.append(
                f"IPC is {self.metrics.ipc:.2f}, below the theoretical maximum. "
                "Look for opportunities to increase parallelism."
            )

        return recommendations

    def export_report(self, filepath: Path, format: str = "json") -> None:
        """
        Export performance report to file.
        
        Args:
            filepath: Output file path
            format: Output format ('json', 'csv', or 'txt')
        """
        summary = self.get_performance_summary()
        recommendations = self.generate_recommendations()

        if format == "json":
            report = {
                'summary': summary,
                'recommendations': recommendations,
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
            }
            with open(filepath, 'w') as f:
                json.dump(report, f, indent=2)

        elif format == "csv":
            # Flatten metrics for CSV
            with open(filepath, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['Metric', 'Value'])

                # Write basic metrics
                for category, metrics in summary.items():
                    if isinstance(metrics, dict):
                        for metric, value in metrics.items():
                            writer.writerow([f"{category}.{metric}", value])

                # Write recommendations
                writer.writerow([])
                writer.writerow(['Recommendations'])
                for rec in recommendations:
                    writer.writerow([rec])

        else:  # txt format
            with open(filepath, 'w') as f:
                f.write("=== SUPERSCALAR PIPELINE PERFORMANCE REPORT ===\n")
                f.write(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")

                # Write summary sections
                for category, metrics in summary.items():
                    f.write(f"\n{category.upper().replace('_', ' ')}:\n")
                    f.write("-" * 40 + "\n")

                    if isinstance(metrics, dict):
                        for metric, value in metrics.items():
                            f.write(f"  {metric}: {value}\n")
                    else:
                        f.write(f"  {metrics}\n")

                # Write recommendations
                f.write("\n\nRECOMMENDATIONS:\n")
                f.write("-" * 40 + "\n")
                for i, rec in enumerate(recommendations, 1):
                    f.write(f"{i}. {rec}\n")

    def plot_performance_trends(self) -> None:
        """Generate performance trend plots."""
        try:
            import matplotlib.pyplot as plt

            fig, axes = plt.subplots(2, 2, figsize=(12, 10))
            fig.suptitle('Pipeline Performance Trends', fontsize=16)

            # IPC over time
            if self.ipc_history:
                axes[0, 0].plot(list(self.ipc_history))
                axes[0, 0].set_title('Instructions Per Cycle (IPC)')
                axes[0, 0].set_xlabel('Cycle')
                axes[0, 0].set_ylabel('IPC')
                axes[0, 0].grid(True, alpha=0.3)

            # Branch accuracy
            if self.branch_accuracy_history:
                axes[0, 1].plot(list(self.branch_accuracy_history))
                axes[0, 1].set_title('Branch Prediction Accuracy')
                axes[0, 1].set_xlabel('Prediction Count')
                axes[0, 1].set_ylabel('Accuracy (%)')
                axes[0, 1].grid(True, alpha=0.3)

            # Instruction mix pie chart
            inst_mix = self.get_performance_summary()['instruction_mix']
            if sum(inst_mix.values()) > 0:
                axes[1, 0].pie(inst_mix.values(), labels=inst_mix.keys(),
                             autopct='%1.1f%%')
                axes[1, 0].set_title('Instruction Mix')

            # Stall breakdown
            stalls = self.get_performance_summary()['stall_analysis']
            stall_types = ['data_stalls', 'structural_stalls', 'control_stalls']
            stall_values = [stalls[st] for st in stall_types]
            if sum(stall_values) > 0:
                axes[1, 1].bar(stall_types, stall_values)
                axes[1, 1].set_title('Pipeline Stalls by Type')
                axes[1, 1].set_ylabel('Cycles')
                axes[1, 1].tick_params(axis='x', rotation=45)

            plt.tight_layout()
            plt.show()

        except ImportError:
            print("Matplotlib not available for plotting")


class PerformanceOptimizer:
    """
    Analyzes performance data and suggests optimizations.
    """

    def __init__(self, profiler: PerformanceProfiler) -> None:
        self.profiler = profiler

    def analyze_branch_patterns(self) -> Dict[str, Any]:
        """Analyze branch prediction patterns."""
        # Group branches by behavior
        always_taken = []
        always_not_taken = []
        biased_taken = []
        biased_not_taken = []
        random_branches = []

        # Analysis would go here based on profiler data

        return {
            'always_taken': always_taken,
            'always_not_taken': always_not_taken,
            'biased_taken': biased_taken,
            'biased_not_taken': biased_not_taken,
            'random': random_branches
        }

    def suggest_compiler_optimizations(self) -> List[str]:
        """Suggest compiler-level optimizations."""
        suggestions = []

        # Check for optimization opportunities
        summary = self.profiler.get_performance_summary()

        # Loop unrolling
        if summary['branch_performance']['predictions'] > 1000:
            suggestions.append(
                "Consider loop unrolling to reduce branch instructions "
                "and improve instruction-level parallelism."
            )

        # Instruction scheduling
        if summary['stall_analysis']['data_stalls'] > summary['basic_metrics']['total_cycles'] * 0.1:
            suggestions.append(
                "Reorder independent instructions to reduce data dependencies "
                "and minimize pipeline stalls."
            )

        # Function inlining
        if 'JAL' in self.profiler.instruction_counts and \
           self.profiler.instruction_counts['JAL'] > 100:
            suggestions.append(
                "Consider function inlining for frequently called small functions "
                "to reduce call/return overhead."
            )

        return suggestions
