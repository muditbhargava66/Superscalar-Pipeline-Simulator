"""
Benchmark runner for automated performance testing and comparison.

This module provides tools for running multiple benchmarks, comparing
performance across different configurations, and generating comprehensive
performance reports.
"""

from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import asdict, dataclass
import json
from pathlib import Path
import time
from typing import Any, Optional

from .performance_profiler import PerformanceProfiler, ProfileResult


@dataclass
class BenchmarkConfig:
    """Configuration for a single benchmark run."""
    
    name: str
    config_file: str
    benchmark_file: str
    max_cycles: Optional[int] = None
    enable_profiling: bool = True
    enable_visualization: bool = False
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class BenchmarkResult:
    """Results from a single benchmark run."""
    
    config: BenchmarkConfig
    success: bool
    execution_time: float
    profile_result: Optional[ProfileResult] = None
    error_message: Optional[str] = None
    simulation_stats: Optional[dict[str, Any]] = None
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        result = {
            'config': self.config.to_dict(),
            'success': self.success,
            'execution_time': self.execution_time,
            'error_message': self.error_message,
            'simulation_stats': self.simulation_stats,
        }
        
        if self.profile_result:
            result['profile_result'] = self.profile_result.to_dict()
        
        return result


class BenchmarkRunner:
    """
    Automated benchmark runner for performance testing.
    
    Supports running multiple benchmarks in parallel, comparing results,
    and generating comprehensive performance reports.
    """
    
    def __init__(self, output_dir: str | Path = "benchmark_results"):
        """
        Initialize benchmark runner.
        
        Args:
            output_dir: Directory for storing benchmark results
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.results: list[BenchmarkResult] = []
    
    def add_benchmark(self, config: BenchmarkConfig) -> None:
        """
        Add a benchmark configuration to the test suite.
        
        Args:
            config: Benchmark configuration
        """
        # Validate configuration
        config_path = Path(config.config_file)
        benchmark_path = Path(config.benchmark_file)
        
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")
        if not benchmark_path.exists():
            raise FileNotFoundError(f"Benchmark file not found: {benchmark_path}")
    
    def run_single_benchmark(self, config: BenchmarkConfig) -> BenchmarkResult:
        """
        Run a single benchmark.
        
        Args:
            config: Benchmark configuration
            
        Returns:
            Benchmark results
        """
        start_time = time.time()
        
        try:
            # Import here to avoid circular imports
            from ..config import ConfigManager
            from ..main import main as simulator_main
            
            # Load configuration
            config_manager = ConfigManager()
            sim_config = config_manager.load_from_file(config.config_file)
            
            # Override max_cycles if specified
            if config.max_cycles:
                sim_config.simulation.max_cycles = config.max_cycles
            
            # Set up profiling
            profiler = None
            profile_result = None
            
            if config.enable_profiling:
                profiler = PerformanceProfiler()
                profiler.start_profiling()
            
            # Run simulation
            # Note: This is a simplified version - actual implementation
            # would need to integrate with the main simulator
            simulation_stats = self._run_simulation(sim_config, config.benchmark_file)
            
            # Stop profiling
            if profiler:
                profile_result = profiler.stop_profiling()
            
            execution_time = time.time() - start_time
            
            return BenchmarkResult(
                config=config,
                success=True,
                execution_time=execution_time,
                profile_result=profile_result,
                simulation_stats=simulation_stats,
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            
            return BenchmarkResult(
                config=config,
                success=False,
                execution_time=execution_time,
                error_message=str(e),
            )
    
    def run_benchmarks(self, configs: list[BenchmarkConfig],
                      parallel: bool = True, max_workers: Optional[int] = None) -> list[BenchmarkResult]:
        """
        Run multiple benchmarks.
        
        Args:
            configs: List of benchmark configurations
            parallel: Run benchmarks in parallel
            max_workers: Maximum number of parallel workers
            
        Returns:
            List of benchmark results
        """
        results = []
        
        if parallel and len(configs) > 1:
            # Run benchmarks in parallel
            with ProcessPoolExecutor(max_workers=max_workers) as executor:
                future_to_config = {
                    executor.submit(self.run_single_benchmark, config): config
                    for config in configs
                }
                
                for future in as_completed(future_to_config):
                    result = future.result()
                    results.append(result)
                    print(f"Completed benchmark: {result.config.name}")
        else:
            # Run benchmarks sequentially
            for config in configs:
                print(f"Running benchmark: {config.name}")
                result = self.run_single_benchmark(config)
                results.append(result)
        
        self.results.extend(results)
        return results
    
    def _run_simulation(self, config, benchmark_file: str) -> dict[str, Any]:
        """
        Run the actual simulation (placeholder implementation).
        
        Args:
            config: Simulator configuration
            benchmark_file: Path to benchmark file
            
        Returns:
            Simulation statistics
        """
        # This is a placeholder - actual implementation would
        # integrate with the main simulator
        return {
            'instructions_executed': 1000,
            'cycles': 1200,
            'ipc': 0.83,
            'branch_prediction_accuracy': 85.5,
            'cache_hit_rate': 92.3,
        }
    
    def compare_results(self, baseline_name: str) -> dict[str, Any]:
        """
        Compare benchmark results against a baseline.
        
        Args:
            baseline_name: Name of the baseline benchmark
            
        Returns:
            Comparison results
        """
        baseline_result = None
        for result in self.results:
            if result.config.name == baseline_name:
                baseline_result = result
                break
        
        if not baseline_result:
            raise ValueError(f"Baseline benchmark '{baseline_name}' not found")
        
        if not baseline_result.success:
            raise ValueError(f"Baseline benchmark '{baseline_name}' failed")
        
        comparisons = []
        
        for result in self.results:
            if result.config.name == baseline_name or not result.success:
                continue
            
            comparison = self._compare_single_result(baseline_result, result)
            comparisons.append(comparison)
        
        return {
            'baseline': baseline_name,
            'comparisons': comparisons,
        }
    
    def _compare_single_result(self, baseline: BenchmarkResult,
                             target: BenchmarkResult) -> dict[str, Any]:
        """Compare two benchmark results."""
        comparison = {
            'name': target.config.name,
            'execution_time_ratio': target.execution_time / baseline.execution_time,
            'performance_delta': {},
        }
        
        # Compare simulation statistics
        if baseline.simulation_stats and target.simulation_stats:
            for key in baseline.simulation_stats:
                if key in target.simulation_stats:
                    baseline_val = baseline.simulation_stats[key]
                    target_val = target.simulation_stats[key]
                    
                    if isinstance(baseline_val, int | float) and baseline_val != 0:
                        ratio = target_val / baseline_val
                        comparison['performance_delta'][key] = {
                            'baseline': baseline_val,
                            'target': target_val,
                            'ratio': ratio,
                            'improvement': (ratio - 1) * 100,  # Percentage improvement
                        }
        
        return comparison
    
    def generate_report(self, output_file: str | Path) -> None:
        """
        Generate a comprehensive benchmark report.
        
        Args:
            output_file: Path to output report file
        """
        report_data = {
            'timestamp': time.time(),
            'total_benchmarks': len(self.results),
            'successful_benchmarks': sum(1 for r in self.results if r.success),
            'failed_benchmarks': sum(1 for r in self.results if not r.success),
            'results': [result.to_dict() for result in self.results],
        }
        
        # Add summary statistics
        successful_results = [r for r in self.results if r.success]
        if successful_results:
            execution_times = [r.execution_time for r in successful_results]
            report_data['summary'] = {
                'average_execution_time': sum(execution_times) / len(execution_times),
                'min_execution_time': min(execution_times),
                'max_execution_time': max(execution_times),
            }
        
        # Save report
        output_path = Path(output_file)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, default=str)
        
        print(f"Benchmark report saved to: {output_path}")
    
    def generate_html_report(self, output_file: str | Path) -> None:
        """
        Generate an HTML benchmark report with visualizations.
        
        Args:
            output_file: Path to output HTML file
        """
        html_content = self._generate_html_content()
        
        output_path = Path(output_file)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"HTML benchmark report saved to: {output_path}")
    
    def _generate_html_content(self) -> str:
        """Generate HTML content for the benchmark report."""
        successful_results = [r for r in self.results if r.success]
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Benchmark Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .summary {{ background: #f0f0f0; padding: 15px; border-radius: 5px; }}
        .benchmark {{ margin: 20px 0; padding: 15px; border: 1px solid #ddd; }}
        .success {{ border-left: 5px solid #4CAF50; }}
        .failure {{ border-left: 5px solid #f44336; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
    </style>
</head>
<body>
    <h1>Benchmark Report</h1>
    
    <div class="summary">
        <h2>Summary</h2>
        <p>Total Benchmarks: {len(self.results)}</p>
        <p>Successful: {len(successful_results)}</p>
        <p>Failed: {len(self.results) - len(successful_results)}</p>
    </div>
    
    <h2>Results</h2>
"""
        
        for result in self.results:
            status_class = "success" if result.success else "failure"
            status_text = "SUCCESS" if result.success else "FAILED"
            
            html += f"""
    <div class="benchmark {status_class}">
        <h3>{result.config.name} - {status_text}</h3>
        <p>Execution Time: {result.execution_time:.2f}s</p>
"""
            
            if result.success and result.simulation_stats:
                html += """
        <table>
            <tr><th>Metric</th><th>Value</th></tr>
"""
                for key, value in result.simulation_stats.items():
                    html += f"            <tr><td>{key}</td><td>{value}</td></tr>\n"
                html += "        </table>\n"
            
            if not result.success and result.error_message:
                html += f"        <p><strong>Error:</strong> {result.error_message}</p>\n"
            
            html += "    </div>\n"
        
        html += """
</body>
</html>
"""
        
        return html
