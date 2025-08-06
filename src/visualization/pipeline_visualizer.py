"""
Pipeline Visualization Module

This module provides real-time visualization of the pipeline execution,
showing instructions flowing through stages and various performance metrics.

Author: Mudit Bhargava
Date: August2025
Python Version: 3.10+
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
import queue
from typing import Any

from matplotlib import animation
from matplotlib.patches import Rectangle
import matplotlib.pyplot as plt


@dataclass
class PipelineSnapshot:
    """Represents the state of the pipeline at a specific cycle."""
    cycle: int
    fetch: List[str]
    decode: List[str]
    issue: List[str]
    execute: List[str]
    memory: List[str]
    writeback: List[str]
    branch_prediction_accuracy: float
    ipc: float
    stalls: int
    cache_hits: int
    cache_misses: int


class PipelineVisualizer:
    """
    Real-time visualization of the superscalar pipeline.
    
    Shows:
    - Instructions in each pipeline stage
    - Performance metrics (IPC, branch accuracy, cache hit rate)
    - Stall and hazard indicators
    - Resource utilization
    """

    def __init__(self, fetch_width: int = 4, issue_width: int = 4) -> None:
        """
        Initialize the pipeline visualizer.
        
        Args:
            fetch_width: Number of instructions fetched per cycle
            issue_width: Number of instructions issued per cycle
        """
        self.fetch_width = fetch_width
        self.issue_width = issue_width

        # Initialize plot
        self.fig, (self.ax_pipeline, self.ax_metrics) = plt.subplots(
            2, 1, figsize=(14, 10), gridspec_kw={'height_ratios': [3, 1]}
        )

        # Pipeline visualization setup
        self.ax_pipeline.set_xlim(0, 10)
        self.ax_pipeline.set_ylim(0, 7)
        self.ax_pipeline.set_aspect('equal')
        self.ax_pipeline.axis('off')

        # Metrics visualization setup
        self.ax_metrics.set_xlim(0, 100)
        self.ax_metrics.set_ylim(0, 100)
        self.ax_metrics.set_xlabel('Cycle')
        self.ax_metrics.set_ylabel('Percentage')
        self.ax_metrics.legend(['IPC*20', 'Branch Acc', 'Cache Hit'])

        # Stage positions
        self.stage_positions = {
            'Fetch': (0.5, 5),
            'Decode': (2, 5),
            'Issue': (3.5, 5),
            'Execute': (5, 5),
            'Memory': (6.5, 5),
            'WriteBack': (8, 5)
        }

        # Data storage
        self.history_length = 100
        self.ipc_history = deque(maxlen=self.history_length)
        self.branch_acc_history = deque(maxlen=self.history_length)
        self.cache_hit_history = deque(maxlen=self.history_length)
        self.cycle_history = deque(maxlen=self.history_length)

        # Thread-safe queue for updates
        self.update_queue: queue.Queue[PipelineSnapshot] = queue.Queue()

        # Draw static elements
        self._draw_pipeline_structure()

        # Animation
        self.animation = None

    def _draw_pipeline_structure(self) -> None:
        """Draw the static pipeline structure."""
        # Draw stage boxes
        for stage_name, (x, y) in self.stage_positions.items():
            rect = Rectangle((x-0.4, y-0.3), 0.8, 0.6,
                           fill=False, edgecolor='black', linewidth=2)
            self.ax_pipeline.add_patch(rect)
            self.ax_pipeline.text(x, y+0.5, stage_name,
                                ha='center', va='bottom', fontsize=10, fontweight='bold')

        # Draw connections between stages
        positions = list(self.stage_positions.values())
        for i in range(len(positions)-1):
            x1, y1 = positions[i]
            x2, y2 = positions[i+1]
            self.ax_pipeline.arrow(x1+0.4, y1, x2-x1-0.8, 0,
                                 head_width=0.1, head_length=0.1, fc='gray', ec='gray')

        # Draw functional units
        self._draw_functional_units()

    def _draw_functional_units(self) -> None:
        """Draw functional units below the execute stage."""
        exec_x, exec_y = self.stage_positions['Execute']

        # ALU units
        for i in range(2):
            rect = Rectangle((exec_x-0.3+i*0.6, exec_y-1.2), 0.5, 0.4,
                           fill=True, facecolor='lightblue', edgecolor='blue')
            self.ax_pipeline.add_patch(rect)
            self.ax_pipeline.text(exec_x+i*0.6, exec_y-1, f'ALU{i}',
                                ha='center', va='center', fontsize=8)

        # FPU
        rect = Rectangle((exec_x-0.3, exec_y-1.8), 0.5, 0.4,
                       fill=True, facecolor='lightgreen', edgecolor='green')
        self.ax_pipeline.add_patch(rect)
        self.ax_pipeline.text(exec_x, exec_y-1.6, 'FPU',
                            ha='center', va='center', fontsize=8)

        # LSU
        rect = Rectangle((exec_x+0.3, exec_y-1.8), 0.5, 0.4,
                       fill=True, facecolor='lightyellow', edgecolor='orange')
        self.ax_pipeline.add_patch(rect)
        self.ax_pipeline.text(exec_x+0.6, exec_y-1.6, 'LSU',
                            ha='center', va='center', fontsize=8)

    def update(self, snapshot: PipelineSnapshot) -> None:
        """
        Update the visualization with a new pipeline snapshot.
        
        Args:
            snapshot: Current state of the pipeline
        """
        self.update_queue.put(snapshot)

    def _animate(self, frame: int) -> None:
        """Animation update function."""
        # Process all pending updates
        updates_processed = 0
        while not self.update_queue.empty() and updates_processed < 5:
            try:
                snapshot = self.update_queue.get_nowait()
                self._update_visualization(snapshot)
                updates_processed += 1
            except queue.Empty:
                break

    def _update_visualization(self, snapshot: PipelineSnapshot) -> None:
        """Update the visualization with new data."""
        # Clear previous instruction text
        for text in self.ax_pipeline.texts[:]:
            if text.get_position()[1] < 4.5:  # Only remove instruction text
                text.remove()

        # Update pipeline stages
        self._draw_stage_contents('Fetch', snapshot.fetch)
        self._draw_stage_contents('Decode', snapshot.decode)
        self._draw_stage_contents('Issue', snapshot.issue)
        self._draw_stage_contents('Execute', snapshot.execute)
        self._draw_stage_contents('Memory', snapshot.memory)
        self._draw_stage_contents('WriteBack', snapshot.writeback)

        # Update metrics
        self.cycle_history.append(snapshot.cycle)
        self.ipc_history.append(snapshot.ipc * 20)  # Scale for visibility
        self.branch_acc_history.append(snapshot.branch_prediction_accuracy)
        cache_hit_rate = (snapshot.cache_hits /
                         (snapshot.cache_hits + snapshot.cache_misses + 1e-6)) * 100
        self.cache_hit_history.append(cache_hit_rate)

        # Redraw metrics plot
        self.ax_metrics.clear()
        if len(self.cycle_history) > 1:
            cycles = list(self.cycle_history)
            self.ax_metrics.plot(cycles, list(self.ipc_history), 'b-', label='IPC×20')
            self.ax_metrics.plot(cycles, list(self.branch_acc_history), 'g-', label='Branch Acc %')
            self.ax_metrics.plot(cycles, list(self.cache_hit_history), 'r-', label='Cache Hit %')
            self.ax_metrics.set_xlim(max(0, cycles[0]), cycles[-1] + 1)
            self.ax_metrics.set_ylim(0, 105)
            self.ax_metrics.set_xlabel('Cycle')
            self.ax_metrics.set_ylabel('Percentage')
            self.ax_metrics.legend()
            self.ax_metrics.grid(True, alpha=0.3)

        # Add current stats text
        stats_text = (f"Cycle: {snapshot.cycle} | "
                     f"IPC: {snapshot.ipc:.2f} | "
                     f"Stalls: {snapshot.stalls}")
        self.ax_pipeline.text(5, 6.5, stats_text,
                            ha='center', va='center', fontsize=10,
                            bbox=dict(boxstyle="round,pad=0.3", facecolor="wheat"))

    def _draw_stage_contents(self, stage_name: str, instructions: List[str]) -> None:
        """Draw instructions in a pipeline stage."""
        x, y = self.stage_positions[stage_name]

        # Draw instructions vertically
        for i, inst in enumerate(instructions[:4]):  # Max 4 instructions shown
            if inst and inst != "NOP":
                self.ax_pipeline.text(x, y - 0.2 - i*0.15, inst,
                                    ha='center', va='center', fontsize=7)

    def start(self) -> None:
        """Start the visualization animation."""
        self.animation = animation.FuncAnimation(
            self.fig, self._animate, interval=100, blit=False
        )
        plt.show(block=False)

    def stop(self) -> None:
        """Stop the visualization."""
        if self.animation:
            self.animation.event_source.stop()
        plt.close(self.fig)


class HazardVisualizer:
    """
    Visualizes pipeline hazards and their resolution.
    
    Shows:
    - Data hazards (RAW, WAR, WAW)
    - Control hazards (branch mispredictions)
    - Structural hazards (resource conflicts)
    - Forwarding paths
    """

    def __init__(self) -> None:
        """Initialize the hazard visualizer."""
        self.fig, self.ax = plt.subplots(figsize=(12, 8))
        self.hazard_history: List[Dict] = []

    def add_hazard(self, cycle: int, hazard_type: str,
                   source: str, destination: str, resolution: str) -> None:
        """
        Record a hazard event.
        
        Args:
            cycle: Cycle when hazard occurred
            hazard_type: Type of hazard (RAW, WAR, WAW, Control, Structural)
            source: Source of hazard
            destination: Affected instruction/stage
            resolution: How the hazard was resolved
        """
        self.hazard_history.append({
            'cycle': cycle,
            'type': hazard_type,
            'source': source,
            'destination': destination,
            'resolution': resolution
        })

    def visualize_hazards(self, start_cycle: int = 0, end_cycle: int = 100) -> None:
        """Create a visualization of hazards over time."""
        # Filter hazards in range
        hazards = [h for h in self.hazard_history
                  if start_cycle <= h['cycle'] <= end_cycle]

        if not hazards:
            print("No hazards to visualize in the specified range")
            return

        # Group by type
        hazard_types = {}
        for h in hazards:
            if h['type'] not in hazard_types:
                hazard_types[h['type']] = []
            hazard_types[h['type']].append(h['cycle'])

        # Create timeline plot
        self.ax.clear()
        colors = {
            'RAW': 'red',
            'WAR': 'orange',
            'WAW': 'yellow',
            'Control': 'blue',
            'Structural': 'green'
        }

        y_pos = 0
        for hazard_type, cycles in hazard_types.items():
            color = colors.get(hazard_type, 'gray')
            self.ax.scatter(cycles, [y_pos] * len(cycles),
                          c=color, s=100, label=hazard_type)
            y_pos += 1

        self.ax.set_xlim(start_cycle - 5, end_cycle + 5)
        self.ax.set_ylim(-0.5, len(hazard_types) - 0.5)
        self.ax.set_xlabel('Cycle')
        self.ax.set_yticks(range(len(hazard_types)))
        self.ax.set_yticklabels(list(hazard_types.keys()))
        self.ax.set_title('Pipeline Hazards Timeline')
        self.ax.legend()
        self.ax.grid(True, alpha=0.3)

        plt.tight_layout()
        plt.show()

    def generate_hazard_report(self) -> Dict[str, Any]:
        """Generate a comprehensive hazard analysis report."""
        if not self.hazard_history:
            return {"error": "No hazard data available"}

        # Count hazards by type
        hazard_counts = {}
        resolution_counts = {}

        for h in self.hazard_history:
            # Count by type
            hazard_counts[h['type']] = hazard_counts.get(h['type'], 0) + 1

            # Count by resolution method
            res_key = f"{h['type']}_{h['resolution']}"
            resolution_counts[res_key] = resolution_counts.get(res_key, 0) + 1

        # Calculate statistics
        total_hazards = len(self.hazard_history)
        cycles = [h['cycle'] for h in self.hazard_history]
        cycle_range = max(cycles) - min(cycles) + 1 if cycles else 1

        report = {
            'total_hazards': total_hazards,
            'hazards_per_cycle': total_hazards / cycle_range,
            'hazard_counts': hazard_counts,
            'resolution_methods': resolution_counts,
            'most_common_hazard': max(hazard_counts, key=hazard_counts.get),
            'cycle_range': (min(cycles), max(cycles)) if cycles else (0, 0)
        }

        return report


def create_performance_dashboard(simulator_stats: Dict[str, Any]) -> None:
    """
    Create a comprehensive performance dashboard.
    
    Args:
        simulator_stats: Dictionary containing various performance statistics
    """
    fig = plt.figure(figsize=(15, 10))
    fig.suptitle('Superscalar Pipeline Performance Dashboard', fontsize=16)

    # IPC over time
    ax1 = plt.subplot(2, 3, 1)
    cycles = simulator_stats.get('cycles', [])
    ipc_values = simulator_stats.get('ipc_history', [])
    ax1.plot(cycles, ipc_values, 'b-')
    ax1.set_title('Instructions Per Cycle (IPC)')
    ax1.set_xlabel('Cycle')
    ax1.set_ylabel('IPC')
    ax1.grid(True, alpha=0.3)

    # Branch prediction accuracy
    ax2 = plt.subplot(2, 3, 2)
    branch_acc = simulator_stats.get('branch_accuracy_history', [])
    ax2.plot(cycles, branch_acc, 'g-')
    ax2.set_title('Branch Prediction Accuracy')
    ax2.set_xlabel('Cycle')
    ax2.set_ylabel('Accuracy (%)')
    ax2.set_ylim(0, 105)
    ax2.grid(True, alpha=0.3)

    # Cache performance
    ax3 = plt.subplot(2, 3, 3)
    cache_hits = simulator_stats.get('cache_hits', 0)
    cache_misses = simulator_stats.get('cache_misses', 0)
    labels = ['Hits', 'Misses']
    sizes = [cache_hits, cache_misses]
    colors = ['green', 'red']
    ax3.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%')
    ax3.set_title('Cache Performance')

    # Functional unit utilization
    ax4 = plt.subplot(2, 3, 4)
    fu_utilization = simulator_stats.get('fu_utilization', {})
    units = list(fu_utilization.keys())
    utilization = list(fu_utilization.values())
    ax4.bar(units, utilization)
    ax4.set_title('Functional Unit Utilization')
    ax4.set_ylabel('Utilization (%)')
    ax4.set_ylim(0, 105)

    # Instruction mix
    ax5 = plt.subplot(2, 3, 5)
    inst_mix = simulator_stats.get('instruction_mix', {})
    if inst_mix:
        labels = list(inst_mix.keys())
        sizes = list(inst_mix.values())
        ax5.pie(sizes, labels=labels, autopct='%1.1f%%')
        ax5.set_title('Instruction Mix')

    # Stall analysis
    ax6 = plt.subplot(2, 3, 6)
    stall_types = simulator_stats.get('stall_types', {})
    if stall_types:
        types = list(stall_types.keys())
        counts = list(stall_types.values())
        ax6.bar(types, counts)
        ax6.set_title('Pipeline Stalls by Type')
        ax6.set_ylabel('Count')
        ax6.tick_params(axis='x', rotation=45)

    plt.tight_layout()
    plt.show()
