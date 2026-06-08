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

            # Extract hazard stats
            hazard_stats = res.get("hazard_stats", {})
            stalls_by_reason = hazard_stats.get("stalls_by_reason", {})
            # Ensure keys exist or default to 0
            # StallReason enum strings might be represented as strings or Enums. Let's convert to string keys.
            stall_dict = {str(k).split(".")[-1]: v for k, v in stalls_by_reason.items()}

            data_hazards = stall_dict.get("DATA_HAZARD", 0)
            structural_hazards = stall_dict.get(
                "STRUCTURAL_HAZARD", 0
            ) + stall_dict.get("RESOURCE_UNAVAILABLE", 0)
            control_hazards = stall_dict.get("CONTROL_HAZARD", 0) + stall_dict.get(
                "BRANCH_MISPREDICTION", 0
            )
            cache_misses = stall_dict.get("CACHE_MISS", 0)

            results_data.append(
                {
                    "name": asm_file.name.replace(".asm", ""),
                    "ipc": res.get("ipc", 0),
                    "cycles": res.get("cycles", 0),
                    "branch_accuracy": res.get("branch_accuracy", 0),
                    "cache_hit_rate": res.get("cache_hit_rate", 0),
                    "energy_pJ": res.get("energy_per_instruction_pJ", 0),
                    "stalls_data": data_hazards,
                    "stalls_structural": structural_hazards,
                    "stalls_control": control_hazards,
                    "stalls_cache": cache_misses,
                }
            )
        except Exception as e:
            print(f"Error running {asm_file.name}: {e}")

    # Extract arrays for plotting
    names = [r["name"] for r in results_data]
    ipcs = [r["ipc"] for r in results_data]
    accuracies = [r["branch_accuracy"] for r in results_data]
    cache_hits = [r["cache_hit_rate"] for r in results_data]
    energies = [r["energy_pJ"] for r in results_data]

    # --- FIGURE 1: 2x2 Core Metrics Grid ---
    plt.style.use("dark_background")
    fig, axs = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle("Superscalar Pipeline Simulator Benchmark Results", fontsize=16)

    x = np.arange(len(names))

    # Top-Left: IPC
    axs[0, 0].bar(x, ipcs, color="#4EC9B0")
    axs[0, 0].set_title("Instructions Per Cycle (IPC)")
    axs[0, 0].set_xticks(x)
    axs[0, 0].set_xticklabels(names, rotation=45, ha="right")
    axs[0, 0].grid(axis="y", linestyle="--", alpha=0.3)

    # Top-Right: Branch Accuracy
    axs[0, 1].bar(x, accuracies, color="#569CD6")
    axs[0, 1].set_title("Branch Prediction Accuracy (%)")
    axs[0, 1].set_ylim(0, 105)
    axs[0, 1].set_xticks(x)
    axs[0, 1].set_xticklabels(names, rotation=45, ha="right")
    axs[0, 1].grid(axis="y", linestyle="--", alpha=0.3)

    # Bottom-Left: Cache Hit Rate
    axs[1, 0].bar(x, cache_hits, color="#DCDCAA")
    axs[1, 0].set_title("L1 Cache Hit Rate (%)")
    axs[1, 0].set_ylim(0, 105)
    axs[1, 0].set_xticks(x)
    axs[1, 0].set_xticklabels(names, rotation=45, ha="right")
    axs[1, 0].grid(axis="y", linestyle="--", alpha=0.3)

    # Bottom-Right: EPI
    axs[1, 1].bar(x, energies, color="#CE9178")
    axs[1, 1].set_title("Energy Per Instruction (pJ)")
    axs[1, 1].set_xticks(x)
    axs[1, 1].set_xticklabels(names, rotation=45, ha="right")
    axs[1, 1].grid(axis="y", linestyle="--", alpha=0.3)

    plt.tight_layout()

    # Save graph 1
    Path("artifacts").mkdir(parents=True, exist_ok=True)
    graph_path = "artifacts/benchmark_comparison.png"
    plt.savefig(graph_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Graph saved to {graph_path}")

    # --- FIGURE 2: Stall Breakdown Stacked Bar Chart ---
    fig2, ax = plt.subplots(figsize=(12, 6))

    stalls_data = np.array([r["stalls_data"] for r in results_data])
    stalls_struct = np.array([r["stalls_structural"] for r in results_data])
    stalls_ctrl = np.array([r["stalls_control"] for r in results_data])
    stalls_cache = np.array([r["stalls_cache"] for r in results_data])

    ax.bar(x, stalls_data, label="Data Hazards (RAW/WAR)", color="#C586C0")
    ax.bar(
        x,
        stalls_struct,
        bottom=stalls_data,
        label="Structural Hazards",
        color="#D16969",
    )
    ax.bar(
        x,
        stalls_ctrl,
        bottom=stalls_data + stalls_struct,
        label="Control Hazards",
        color="#B5CEA8",
    )
    ax.bar(
        x,
        stalls_cache,
        bottom=stalls_data + stalls_struct + stalls_ctrl,
        label="Cache Misses",
        color="#4FC1FF",
    )

    ax.set_ylabel("Stall Cycles")
    ax.set_title("Pipeline Stall Breakdown (Hazard Profiling)")
    ax.set_xticks(x)
    ax.set_xticklabels(names, rotation=45, ha="right")
    ax.legend()
    ax.grid(axis="y", linestyle="--", alpha=0.3)

    plt.tight_layout()
    stall_graph_path = "artifacts/stall_breakdown.png"
    plt.savefig(stall_graph_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Stall graph saved to {stall_graph_path}")

    # Save markdown report
    report_path = "artifacts/benchmark_results.md"
    with open(report_path, "w") as f:
        f.write("# Benchmark Suite Results\n\n")
        f.write("![Benchmark Comparison](benchmark_comparison.png)\n\n")
        f.write("![Stall Breakdown](stall_breakdown.png)\n\n")
        f.write("## Detailed Metrics\n\n")
        f.write(
            "| Benchmark | IPC | Cycles | Branch Accuracy | Cache Hit Rate | EPI (pJ) | Total Stalls |\n"
        )
        f.write(
            "|-----------|-----|--------|-----------------|----------------|----------|--------------|\n"
        )
        for r in results_data:
            total_stalls = (
                r["stalls_data"]
                + r["stalls_structural"]
                + r["stalls_control"]
                + r["stalls_cache"]
            )
            f.write(
                f"| {r['name']} | {r['ipc']:.3f} | {r['cycles']} | {r['branch_accuracy']:.1f}% | {r['cache_hit_rate']:.1f}% | {r['energy_pJ']:.1f} | {total_stalls} |\n"
            )

    print(f"Report saved to {report_path}")


if __name__ == "__main__":
    run_all_benchmarks()
