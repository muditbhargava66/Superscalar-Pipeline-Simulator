#!/usr/bin/env python3
"""
Benchmark runner for Superscalar Pipeline Simulator.

Runs all assembly benchmarks and generates:
- artifacts/benchmark_results.md  (markdown report with metrics table)
- artifacts/benchmark_comparison.png  (2x2 core metrics grid)
- artifacts/stall_breakdown.png  (stacked bar chart of stall causes)
"""

# Force non-interactive matplotlib backend BEFORE importing pyplot.
# This prevents failures in headless CI environments (no $DISPLAY).
import matplotlib

matplotlib.use("Agg")

from pathlib import Path
import sys
import traceback

import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).parent / "src"))
from main import SuperscalarSimulator


def run_all_benchmarks():
    benchmark_dir = Path("benchmarks")
    asm_files = list(benchmark_dir.glob("**/*.asm"))

    if not asm_files:
        print("ERROR: No .asm benchmark files found in benchmarks/")
        sys.exit(1)

    print(f"Found {len(asm_files)} benchmarks")

    results_data = []
    errors = []

    for asm_file in sorted(asm_files):
        print(f"Running benchmark: {asm_file.name}...", flush=True)
        try:
            simulator = SuperscalarSimulator("config.yaml")
            simulator.load_program(str(asm_file))
            res = simulator.run_simulation()

            # Extract hazard stats
            hazard_stats = res.get("hazard_stats", {})
            stalls_by_reason = hazard_stats.get("stalls_by_reason", {})
            # StallReason enum keys → string keys (last component after '.')
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
            # Print full traceback so CI logs show exactly what failed
            print(f"ERROR running {asm_file.name}: {e}", file=sys.stderr, flush=True)
            traceback.print_exc(file=sys.stderr)
            errors.append({"name": asm_file.name, "error": str(e)})

    # ---- Plotting (only if we have results) ----
    Path("artifacts").mkdir(parents=True, exist_ok=True)

    if results_data:
        _generate_plots(results_data)
    else:
        print("WARNING: No benchmark results to plot.", file=sys.stderr, flush=True)

    # ---- Markdown report ----
    _generate_report(results_data, errors)


def _generate_plots(results_data: list[dict]) -> None:
    """Generate benchmark comparison PNG charts."""
    names = [r["name"] for r in results_data]
    ipcs = [r["ipc"] for r in results_data]
    accuracies = [r["branch_accuracy"] for r in results_data]
    cache_hits = [r["cache_hit_rate"] for r in results_data]
    energies = [r["energy_pJ"] for r in results_data]

    plt.style.use("dark_background")
    x = np.arange(len(names))

    # --- FIGURE 1: 2x2 Core Metrics Grid ---
    fig, axs = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle("Superscalar Pipeline Simulator Benchmark Results", fontsize=16)

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


def _generate_report(results_data: list[dict], errors: list[dict]) -> None:
    """Generate two markdown reports:
    - artifacts/benchmark_results.md      (full local report with image links)
    - artifacts/benchmark_pr_comment.md   (lightweight text-only for PR comments)
    """
    # ---- Full local report (references local PNG files) ----
    full_path = "artifacts/benchmark_results.md"
    with open(full_path, "w", encoding="utf-8") as f:
        f.write("# Benchmark Suite Results\n\n")
        f.write("![Benchmark Comparison](benchmark_comparison.png)\n\n")
        f.write("![Stall Breakdown](stall_breakdown.png)\n\n")
        _write_table(f, results_data)
        _write_errors(f, errors)
    print(f"Report saved to {full_path}")

    # ---- Lightweight PR comment report (no images, text only) ----
    pr_path = "artifacts/benchmark_pr_comment.md"
    with open(pr_path, "w", encoding="utf-8") as f:
        f.write("**Superscalar Pipeline Simulator — Benchmark Results**\n\n")
        _write_table(f, results_data)
        if errors:
            f.write(
                f"\n**{len(errors)} benchmark(s) failed.** "
                "See workflow logs for full tracebacks.\n\n"
            )
            _write_errors(f, errors)
        f.write(
            "\n_Full visual report (PNG charts) available as a downloadable "
            "workflow artifact._\n"
        )
    print(f"PR comment report saved to {pr_path}")


def _write_table(f, results_data: list[dict]) -> None:
    """Write the benchmark metrics table to a file handle."""
    f.write("## Detailed Metrics\n\n")
    f.write(
        "| Benchmark | IPC | Cycles | Branch Accuracy "
        "| Cache Hit Rate | EPI (pJ) | Total Stalls |\n"
    )
    f.write(
        "|-----------|-----|--------|-----------------"
        "|----------------|----------|--------------|\n"
    )
    if results_data:
        for r in results_data:
            total_stalls = (
                r["stalls_data"]
                + r["stalls_structural"]
                + r["stalls_control"]
                + r["stalls_cache"]
            )
            f.write(
                f"| {r['name']} | {r['ipc']:.3f} | {r['cycles']} | "
                f"{r['branch_accuracy']:.1f}% | {r['cache_hit_rate']:.1f}% | "
                f"{r['energy_pJ']:.1f} | {total_stalls} |\n"
            )
    else:
        f.write("| *No benchmarks completed successfully* | | | | | | |\n")


def _write_errors(f, errors: list[dict]) -> None:
    """Write an error table to a file handle."""
    if not errors:
        return
    f.write("\n## Errors\n\n")
    f.write("| Benchmark | Error |\n")
    f.write("|-----------|-------|\n")
    for e in errors:
        safe_error = e["error"].replace("|", "\\|")
        f.write(f"| {e['name']} | {safe_error} |\n")


if __name__ == "__main__":
    run_all_benchmarks()
