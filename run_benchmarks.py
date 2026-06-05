import glob
import os
from pathlib import Path
import sys

import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).parent / "src"))
from main import SuperscalarSimulator


def run_all_benchmarks():
    benchmark_dir = Path("benchmarks")
    asm_files = list(benchmark_dir.glob("**/*.asm"))
    
    results_data = []
    
    for asm_file in sorted(asm_files):
        print(f"Running benchmark: {asm_file.name}...")
        try:
            simulator = SuperscalarSimulator("config.yaml")
            simulator.load_program(str(asm_file))
            res = simulator.run_simulation()
            
            results_data.append({
                "name": asm_file.name.replace(".asm", ""),
                "ipc": res.get("ipc", 0),
                "cycles": res.get("cycles", 0),
                "branch_accuracy": res.get("branch_accuracy", 0),
                "cache_hit_rate": res.get("cache_hit_rate", 0),
                "energy_pJ": res.get("energy_per_instruction_pJ", 0)
            })
        except Exception as e:
            print(f"Error running {asm_file.name}: {e}")
            
    # Generate visualization
    names = [r["name"] for r in results_data]
    ipcs = [r["ipc"] for r in results_data]
    accuracies = [r["branch_accuracy"] for r in results_data]
    
    plt.style.use('dark_background')
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
    
    # Plot IPC
    x = np.arange(len(names))
    ax1.bar(x, ipcs, color='#4EC9B0')
    ax1.set_ylabel('Instructions Per Cycle (IPC)')
    ax1.set_title('Benchmark Performance Comparison (IPC)')
    ax1.set_xticks(x)
    ax1.set_xticklabels(names, rotation=45, ha='right')
    ax1.grid(axis='y', linestyle='--', alpha=0.3)
    
    # Plot Branch Accuracy
    ax2.bar(x, accuracies, color='#569CD6')
    ax2.set_ylabel('Branch Prediction Accuracy (%)')
    ax2.set_title('Branch Predictor Effectiveness Across Workloads')
    ax2.set_xticks(x)
    ax2.set_xticklabels(names, rotation=45, ha='right')
    ax2.set_ylim(0, 105)
    ax2.grid(axis='y', linestyle='--', alpha=0.3)
    
    plt.tight_layout()
    
    # Save graph
    Path('artifacts').mkdir(parents=True, exist_ok=True)
    graph_path = 'artifacts/benchmark_comparison.png'
    plt.savefig(graph_path, dpi=300, bbox_inches='tight')
    print(f"Graph saved to {graph_path}")
    
    # Save markdown report
    report_path = 'artifacts/benchmark_results.md'
    with open(report_path, 'w') as f:
        f.write("# Benchmark Suite Results\n\n")
        f.write("![Benchmark Comparison](benchmark_comparison.png)\n\n")
        f.write("## Detailed Metrics\n\n")
        f.write("| Benchmark | IPC | Cycles | Branch Accuracy | Cache Hit Rate | EPI (pJ) |\n")
        f.write("|-----------|-----|--------|-----------------|----------------|----------|\n")
        for r in results_data:
            f.write(f"| {r['name']} | {r['ipc']:.3f} | {r['cycles']} | {r['branch_accuracy']:.1f}% | {r['cache_hit_rate']:.1f}% | {r['energy_pJ']:.1f} |\n")
            
    print(f"Report saved to {report_path}")

if __name__ == '__main__':
    run_all_benchmarks()
