"""
Data Forwarding Unit Implementation

This module implements the data forwarding unit that enables bypassing
to reduce data hazards in the pipeline.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import logging
from typing import Any, Optional

# Handle imports for both package and direct execution
try:
    from ..utils.instruction import Instruction
except (ImportError, ValueError):
    import os
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    from utils.instruction import Instruction


@dataclass
class ForwardingPath:
    """Represents a data forwarding path between pipeline stages."""
    from_stage: str
    to_stage: str
    condition: Callable[[Instruction], bool]
    priority: int = 0  # Higher priority paths are checked first


@dataclass
class ForwardedData:
    """Container for forwarded data."""
    source_instruction: Instruction
    register: str
    value: Any
    from_stage: str
    cycle: int


class DataForwardingUnit:
    """
    Data forwarding unit for hazard reduction.
    
    Manages forwarding paths between pipeline stages to bypass
    data through the pipeline and reduce stalls.
    """

    def __init__(self) -> None:
        """Initialize the data forwarding unit."""
        self.forwarding_paths: List[ForwardingPath] = []
        self.forwarding_data: Dict[str, List[ForwardedData]] = {}

        # Statistics
        self.forwards_count = 0
        self.forward_hits = 0
        self.forward_misses = 0

        # Forwarding bus data (current cycle)
        self.current_forwards: Dict[str, Dict[str, Any]] = {}

        logging.debug("Initialized Data Forwarding Unit")

    def add_forwarding_path(self, from_stage: str, to_stage: str,
                           forwarding_condition: Callable[[Instruction], bool],
                           priority: int = 0) -> None:
        """
        Add a forwarding path between pipeline stages.
        
        Args:
            from_stage: Source stage name
            to_stage: Destination stage name
            forwarding_condition: Function to check if forwarding applies
            priority: Priority of this path (higher = checked first)
        """
        path = ForwardingPath(
            from_stage=from_stage,
            to_stage=to_stage,
            condition=forwarding_condition,
            priority=priority
        )
        self.forwarding_paths.append(path)

        # Sort by priority (descending)
        self.forwarding_paths.sort(key=lambda p: p.priority, reverse=True)

        logging.info(f"Added forwarding path: {from_stage} -> {to_stage} (priority {priority})")

    def forward_data(self, instruction: Instruction, stage: str) -> None:
        """
        Make data available for forwarding from a stage.
        
        Args:
            instruction: Instruction producing data
            stage: Current stage of the instruction
        """
        if not instruction or not hasattr(instruction, 'result'):
            return

        # Check if this instruction produces forwardable data
        if instruction.has_destination_register() and instruction.result is not None:
            dest_reg = instruction.get_destination_register()

            # Store forwarding data
            forwarded = ForwardedData(
                source_instruction=instruction,
                register=dest_reg,
                value=instruction.result,
                from_stage=stage,
                cycle=getattr(self, 'current_cycle', 0)
            )

            # Add to current cycle's forwarding data
            if stage not in self.current_forwards:
                self.current_forwards[stage] = {}

            self.current_forwards[stage][dest_reg] = instruction.result

            # Store in forwarding history
            if dest_reg not in self.forwarding_data:
                self.forwarding_data[dest_reg] = []

            self.forwarding_data[dest_reg].append(forwarded)

            # Keep only recent forwarding data (last 5 cycles)
            self.forwarding_data[dest_reg] = self.forwarding_data[dest_reg][-5:]

            self.forwards_count += 1

            logging.debug(f"Forwarding available: {dest_reg} = {instruction.result} from {stage}")

    def get_forwarded_data(self, instruction: Instruction, stage: str) -> Optional[Dict[str, Any]]:
        """
        Get forwarded data for an instruction at a specific stage.
        
        Args:
            instruction: Instruction needing data
            stage: Current stage of the instruction
            
        Returns:
            Dictionary of register -> value mappings or None
        """
        if not instruction:
            return None

        # Get source registers that need data
        source_registers = instruction.get_source_registers()
        if not source_registers:
            return None

        forwarded_values = {}

        # Check each forwarding path (already sorted by priority)
        for path in self.forwarding_paths:
            if path.to_stage != stage:
                continue

            if not path.condition(instruction):
                continue

            # Check if data is available from the source stage
            if path.from_stage in self.current_forwards:
                stage_data = self.current_forwards[path.from_stage]

                for src_reg in source_registers:
                    if src_reg in stage_data and src_reg not in forwarded_values:
                        # Only use this value if we haven't already found a higher priority one
                        forwarded_values[src_reg] = stage_data[src_reg]
                        self.forward_hits += 1

                        logging.debug(f"Forwarding hit: {src_reg} = {stage_data[src_reg]} "
                                    f"from {path.from_stage} to {stage} (priority {path.priority})")

        # Track misses
        for src_reg in source_registers:
            if src_reg not in forwarded_values:
                self.forward_misses += 1

        return forwarded_values if forwarded_values else None

    def apply_forwarding(self, instruction: Instruction, stage: str) -> bool:
        """
        Apply forwarding to an instruction's operands.
        
        Args:
            instruction: Instruction to apply forwarding to
            stage: Current stage
            
        Returns:
            True if forwarding was applied, False otherwise
        """
        forwarded_data = self.get_forwarded_data(instruction, stage)

        if not forwarded_data:
            return False

        # Apply forwarded values
        if not hasattr(instruction, 'forwarded_values'):
            instruction.forwarded_values = {}

        instruction.forwarded_values.update(forwarded_data)

        # Update register values if instruction has them
        if hasattr(instruction, 'register_values'):
            instruction.register_values.update(forwarded_data)

        logging.debug(f"Applied forwarding to {instruction}: {forwarded_data}")

        return True

    def check_dependency(self, consumer: Instruction, producer: Instruction) -> bool:
        """
        Check if consumer instruction depends on producer.
        
        Args:
            consumer: Instruction that may consume data
            producer: Instruction that may produce data
            
        Returns:
            True if dependency exists
        """
        if not producer.has_destination_register():
            return False

        producer_dest = producer.get_destination_register()
        consumer_sources = consumer.get_source_registers()

        return producer_dest in consumer_sources

    def get_operand_value(self, operand: str, stage: str = None) -> Optional[Any]:
        """
        Get the forwarded value for an operand.
        
        Args:
            operand: Register name
            stage: Optional stage filter
            
        Returns:
            Forwarded value or None
        """
        # Check current forwards first
        for from_stage, stage_data in self.current_forwards.items():
            if stage and from_stage != stage:
                continue

            if operand in stage_data:
                return stage_data[operand]

        # Check historical data
        if operand in self.forwarding_data:
            # Get most recent value
            recent = self.forwarding_data[operand][-1]
            return recent.value

        return None

    def clear_cycle_data(self) -> None:
        """Clear forwarding data for the current cycle."""
        self.current_forwards.clear()

    def get_statistics(self) -> Dict[str, Any]:
        """Get forwarding unit statistics."""
        total_requests = self.forward_hits + self.forward_misses
        hit_rate = (self.forward_hits / total_requests * 100) if total_requests > 0 else 0

        return {
            'forwards_created': self.forwards_count,
            'forward_hits': self.forward_hits,
            'forward_misses': self.forward_misses,
            'forward_hit_rate': hit_rate,
            'active_paths': len(self.forwarding_paths),
            'registers_tracked': len(self.forwarding_data)
        }

    def reset(self) -> None:
        """Reset the forwarding unit."""
        self.forwarding_data.clear()
        self.current_forwards.clear()
        self.forwards_count = 0
        self.forward_hits = 0
        self.forward_misses = 0

        logging.info("Data forwarding unit reset")


class AdvancedDataForwardingUnit(DataForwardingUnit):
    """
    Enhanced data forwarding unit with additional features.
    
    Adds:
    - Priority-based forwarding selection
    - Cycle-accurate forwarding timing
    - Forwarding conflict resolution
    """

    def __init__(self) -> None:
        super().__init__()
        self.forwarding_latencies = {
            'execute': 0,      # Same cycle
            'memory': 1,       # Next cycle
            'writeback': 2     # Two cycles later
        }

        # Track forwarding conflicts
        self.conflicts = 0

    def resolve_forwarding_conflict(self, register: str,
                                  sources: List[ForwardedData]) -> ForwardedData:
        """
        Resolve conflicts when multiple sources can forward data.
        
        Args:
            register: Register with conflicting forwards
            sources: List of possible forwarding sources
            
        Returns:
            Selected forwarding source
        """
        if not sources:
            return None

        # Sort by priority:
        # 1. Most recent instruction (highest cycle)
        # 2. Latest pipeline stage
        # 3. Instruction order

        stage_priority = {'writeback': 3, 'memory': 2, 'execute': 1}

        def priority_key(fwd: ForwardedData):
            return (
                fwd.cycle,
                stage_priority.get(fwd.from_stage, 0),
                -getattr(fwd.source_instruction, 'address', 0)
            )

        sources.sort(key=priority_key, reverse=True)

        if len(sources) > 1:
            self.conflicts += 1
            logging.debug(f"Forwarding conflict for {register}, "
                        f"selected from {sources[0].from_stage}")

        return sources[0]

    def get_forwarding_latency(self, from_stage: str, to_stage: str) -> int:
        """
        Get the latency for forwarding between stages.
        
        Args:
            from_stage: Source stage
            to_stage: Destination stage
            
        Returns:
            Latency in cycles
        """
        # Simple model - could be made more sophisticated
        stage_order = ['fetch', 'decode', 'issue', 'execute', 'memory', 'writeback']

        try:
            from_idx = stage_order.index(from_stage)
            to_idx = stage_order.index(to_stage)

            if from_idx >= to_idx:
                return 0  # Same cycle forwarding
            else:
                return from_idx - to_idx  # Negative means not possible
        except ValueError:
            return 1  # Default latency

    def visualize_forwarding_paths(self) -> str:
        """
        Create a visual representation of active forwarding paths.
        
        Returns:
            ASCII art representation of forwarding paths
        """
        lines = ["Active Forwarding Paths:"]
        lines.append("-" * 40)

        for path in self.forwarding_paths:
            arrow = "==>" if path.priority > 0 else "-->"
            lines.append(f"{path.from_stage:>10} {arrow} {path.to_stage:<10} "
                        f"(priority: {path.priority})")

        lines.append("-" * 40)
        lines.append(f"Total paths: {len(self.forwarding_paths)}")
        lines.append(f"Conflicts resolved: {self.conflicts}")

        return "\n".join(lines)
