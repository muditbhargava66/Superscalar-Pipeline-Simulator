#!/usr/bin/env python3

"""
Comprehensive Performance Counters for the Superscalar Pipeline Simulator.

Provides detailed pipeline stall breakdown, hazard counters, cache counters,
branch counters, and ILP tracking.
"""

from typing import Any


class PerformanceCounters:
    """
    Detailed performance counters for pipeline analysis.

    Tracks stall breakdown by stage, hazard types, cache behavior,
    branch prediction accuracy, and instruction-level parallelism metrics.
    """

    def __init__(self) -> None:
        """Initialize all performance counters to zero."""
        # Pipeline stall counters (cycles stalled per stage)
        self.pipeline_stalls: dict[str, int] = {
            "fetch_stalls": 0,
            "decode_stalls": 0,
            "issue_stalls": 0,
            "execute_stalls": 0,
            "memory_stalls": 0,
            "writeback_stalls": 0,
        }

        # Hazard counters
        self.hazard_counts: dict[str, int] = {
            "raw_hazards": 0,
            "war_hazards": 0,
            "waw_hazards": 0,
            "structural_hazards": 0,
            "control_hazards": 0,
        }

        # Cache counters
        self.cache_counters: dict[str, int] = {
            "l1_read_hits": 0,
            "l1_read_misses": 0,
            "l1_write_hits": 0,
            "l1_write_misses": 0,
            "l2_hits": 0,
            "l2_misses": 0,
            "memory_reads": 0,
            "memory_writes": 0,
            "cache_stall_cycles": 0,
        }

        # Branch counters
        self.branch_counters: dict[str, int] = {
            "total_predictions": 0,
            "correct_predictions": 0,
            "mispredictions": 0,
            "misprediction_penalty_cycles": 0,
            "branches_executed": 0,
        }

        # ILP (Instruction-Level Parallelism) counters
        self.ilp_counters: dict[str, int | float] = {
            "instructions_issued": 0,
            "instructions_completed": 0,
            "total_window_size": 0,
            "window_samples": 0,
            "max_instructions_in_flight": 0,
            "multi_issue_cycles": 0,
        }

        # Cycle tracking
        self.total_cycles = 0
        self.busy_cycles = 0

    def update_from_hazard_controller(self, hazard_stats: dict[str, Any]) -> None:
        """
        Update counters from hazard controller statistics.

        Args:
            hazard_stats: Statistics dictionary from HazardController.get_statistics()
        """
        # Update hazard counts
        hazards = hazard_stats.get("hazards_detected", {})
        if isinstance(hazards, dict):
            # HazardType enum keys
            for key, value in hazards.items():
                key_str = str(key).lower()
                if "raw" in key_str:
                    self.hazard_counts["raw_hazards"] = value
                elif "war" in key_str:
                    self.hazard_counts["war_hazards"] = value
                elif "waw" in key_str:
                    self.hazard_counts["waw_hazards"] = value
                elif "structural" in key_str:
                    self.hazard_counts["structural_hazards"] = value
                elif "control" in key_str:
                    self.hazard_counts["control_hazards"] = value

        # Update stall reasons
        stalls = hazard_stats.get("stalls_by_reason", {})
        if isinstance(stalls, dict):
            for key, value in stalls.items():
                key_str = str(key).lower()
                if "data_dependency" in key_str or "raw" in key_str:
                    self.pipeline_stalls["issue_stalls"] += value
                elif "structural" in key_str:
                    self.pipeline_stalls["execute_stalls"] += value
                elif "control" in key_str or "branch" in key_str:
                    self.pipeline_stalls["fetch_stalls"] += value

        # Update instructions completed
        completed = hazard_stats.get("instructions_completed", 0)
        self.ilp_counters["instructions_completed"] = completed

    def update_from_execution_engine(self, exec_stats: dict[str, Any]) -> None:
        """
        Update counters from execution engine statistics.

        Args:
            exec_stats: Statistics dictionary from execution engine get_statistics()
        """
        self.cache_counters["cache_stall_cycles"] = exec_stats.get(
            "cache_stall_cycles", 0
        )
        self.memory_stalls = exec_stats.get("cache_misses", 0)

        # Update branch operations
        branch_ops = exec_stats.get("branch_ops", 0)
        self.branch_counters["branches_executed"] = branch_ops

    def update_from_memory_hierarchy(self, memory_stats: dict[str, Any]) -> None:
        """
        Update counters from memory hierarchy statistics.

        Args:
            memory_stats: Statistics from MemoryHierarchy.get_statistics()
        """
        l1_stats = memory_stats.get("l1_stats", {})
        if isinstance(l1_stats, dict):
            self.cache_counters["l1_read_hits"] = l1_stats.get("hits", 0)
            self.cache_counters["l1_read_misses"] = l1_stats.get("misses", 0)

        l2_stats = memory_stats.get("l2_stats", {})
        if isinstance(l2_stats, dict):
            self.cache_counters["l2_hits"] = l2_stats.get("hits", 0)
            self.cache_counters["l2_misses"] = l2_stats.get("misses", 0)

        self.cache_counters["memory_reads"] = memory_stats.get("memory_accesses", 0)

    def update_from_branch_predictor(self, predictor: Any) -> None:
        """
        Update branch counters from branch predictor.

        Args:
            predictor: Branch predictor instance
        """
        if hasattr(predictor, "total_predictions"):
            self.branch_counters["total_predictions"] = predictor.total_predictions
        if hasattr(predictor, "total_mispredictions"):
            self.branch_counters["mispredictions"] = predictor.total_mispredictions
            self.branch_counters["correct_predictions"] = (
                self.branch_counters["total_predictions"]
                - self.branch_counters["mispredictions"]
            )

    def record_cycle(
        self, instructions_issued: int = 0, instructions_in_flight: int = 0
    ) -> None:
        """
        Record a simulation cycle.

        Args:
            instructions_issued: Number of instructions issued this cycle
            instructions_in_flight: Current number of instructions in pipeline
        """
        self.total_cycles += 1
        if instructions_issued > 0:
            self.busy_cycles += 1

        self.ilp_counters["instructions_issued"] += instructions_issued
        self.ilp_counters["total_window_size"] += instructions_in_flight
        self.ilp_counters["window_samples"] += 1

        self.ilp_counters["max_instructions_in_flight"] = max(
            self.ilp_counters["max_instructions_in_flight"], instructions_in_flight
        )

        if instructions_issued > 1:
            self.ilp_counters["multi_issue_cycles"] += 1

    def record_branch_outcome(
        self, predicted: bool, actual: bool, penalty_cycles: int = 0
    ) -> None:
        """
        Record a branch prediction outcome.

        Args:
            predicted: Predicted direction (True=taken)
            actual: Actual direction (True=taken)
            penalty_cycles: Penalty cycles if mispredicted
        """
        self.branch_counters["total_predictions"] += 1
        if predicted == actual:
            self.branch_counters["correct_predictions"] += 1
        else:
            self.branch_counters["mispredictions"] += 1
            self.branch_counters["misprediction_penalty_cycles"] += penalty_cycles

    def get_detailed_report(self) -> dict[str, Any]:
        """
        Get a comprehensive performance report.

        Returns:
            Structured dictionary with all performance counter data
        """
        # Calculate derived metrics
        avg_window = 0.0
        if self.ilp_counters["window_samples"] > 0:
            avg_window = (
                self.ilp_counters["total_window_size"]
                / self.ilp_counters["window_samples"]
            )

        branch_accuracy = 0.0
        total_pred = self.branch_counters["total_predictions"]
        if total_pred > 0:
            branch_accuracy = (
                self.branch_counters["correct_predictions"] / total_pred
            ) * 100.0

        pipeline_utilization = 0.0
        if self.total_cycles > 0:
            pipeline_utilization = (self.busy_cycles / self.total_cycles) * 100.0

        total_cache_accesses = (
            self.cache_counters["l1_read_hits"]
            + self.cache_counters["l1_read_misses"]
            + self.cache_counters["l1_write_hits"]
            + self.cache_counters["l1_write_misses"]
        )
        l1_hit_rate = 0.0
        if total_cache_accesses > 0:
            l1_hit_rate = (
                (
                    self.cache_counters["l1_read_hits"]
                    + self.cache_counters["l1_write_hits"]
                )
                / total_cache_accesses
                * 100.0
            )

        total_hazards = sum(self.hazard_counts.values())
        total_stalls = sum(self.pipeline_stalls.values())

        return {
            "cycle_counters": {
                "total_cycles": self.total_cycles,
                "busy_cycles": self.busy_cycles,
                "pipeline_utilization_pct": round(pipeline_utilization, 2),
            },
            "pipeline_stalls": {
                **self.pipeline_stalls,
                "total_stall_cycles": total_stalls,
            },
            "hazard_counters": {
                **self.hazard_counts,
                "total_hazards": total_hazards,
            },
            "cache_counters": {
                **self.cache_counters,
                "l1_hit_rate_pct": round(l1_hit_rate, 2),
                "total_l1_accesses": total_cache_accesses,
            },
            "branch_counters": {
                **self.branch_counters,
                "accuracy_pct": round(branch_accuracy, 2),
            },
            "ilp_counters": {
                **self.ilp_counters,
                "average_window_size": round(avg_window, 2),
                "multi_issue_rate_pct": round(
                    (
                        self.ilp_counters["multi_issue_cycles"]
                        / max(self.total_cycles, 1)
                    )
                    * 100.0,
                    2,
                ),
            },
        }

    def reset(self) -> None:
        """Reset all counters to zero."""
        self.__init__()  # type: ignore[misc]
