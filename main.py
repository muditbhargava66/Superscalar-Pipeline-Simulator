#!/usr/bin/env python3
"""
Superscalar Pipeline Simulator - Advanced Cycle-Accurate Implementation

A comprehensive, cycle-accurate superscalar pipeline simulator for computer
architecture research and education. This simulator provides realistic
modeling of modern processor features with detailed timing and performance analysis.

Key Features:
- 6-stage superscalar pipeline (FETCH→DECODE→ISSUE→EXECUTE→MEMORY→WRITEBACK)
- Out-of-order execution with reservation stations and reorder buffer
- Advanced branch prediction (Tournament, Perceptron, Adaptive Hybrid, GShare, Bimodal)
- Non-blocking cache hierarchy with MSHR support
- Enhanced register renaming with precise exception handling
- Comprehensive power and energy modeling with component-level analysis
- Data forwarding with multiple bypass paths (EX→EX, MEM→EX, WB→EX)
- Professional error handling with structured exception hierarchy
- Performance profiling and memory analysis tools
- Pipeline visualization and detailed statistics

Usage Examples:
    python main.py --benchmark benchmarks/matrix_multiplication.asm
    python main.py --config config.yaml --benchmark benchmarks/fibonacci_recursive.asm --visualize
    python main.py --benchmark benchmarks/memory_access_patterns.asm --profile --debug

Author: Mudit Bhargava
Maintained: June 2026
"""

import argparse
import logging
from pathlib import Path
import sys
from typing import Any, Optional

import yaml

# Add src directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Import simulator components
from branch_prediction.always_taken_predictor import AlwaysTakenPredictor
from branch_prediction.bimodal_predictor import BimodalPredictor
from branch_prediction.gshare_predictor import GsharePredictor
from cache.cache import DataCache, InstructionCache, Memory
from cache.enhanced_cache import EnhancedCache, MemoryAccessType, MemoryHierarchy
from data_forwarding.data_forwarding_unit import DataForwardingUnit
from performance.performance_counters import PerformanceCounters
from pipeline.decode_stage import DecodeStage
from pipeline.execute_stage import ExecuteStage, OutOfOrderExecuteStage
from pipeline.fetch_stage import FetchStage
from pipeline.hazard_controller import HazardController
from pipeline.issue_stage import IssueStage
from pipeline.memory_access_stage import MemoryAccessStage
from pipeline.write_back_stage import WriteBackStage
from register_file.register_file import RegisterFile
from register_file.register_renaming import AdvancedRegisterRenaming
from utils.execution_engine import CycleAccurateExecutionEngine, ExecutionResult
from utils.instruction import Instruction, InstructionType
from utils.instruction_parser import MIPSInstructionParser
from utils.instruction_parser import parse_register as _parse_reg
from utils.scoreboard import Scoreboard

# Import enhanced features (with fallback for basic functionality)
try:
    from config import ConfigManager, SimulatorConfig
    from exceptions import (
        ConfigurationError,
        PipelineError,
        SimulatorError,
        create_error_context,
        handle_simulator_error,
    )
    from gui.config_gui import ConfigurationGUI
    from profiling import MemoryProfiler, PerformanceProfiler
    from visualization.pipeline_visualizer import (
        PipelineSnapshot,
        PipelineVisualizer,
        create_performance_dashboard,
    )

    ENHANCED_FEATURES = True
except ImportError:
    # Fallback for basic functionality
    ENHANCED_FEATURES = False
    print("Warning: Enhanced features not available. Using basic functionality.")


class SuperscalarSimulator:
    """
    Main simulator class that orchestrates the superscalar pipeline simulation.

    This class provides both basic and enhanced functionality depending on
    available dependencies. It handles configuration, component initialization,
    program loading, and simulation execution.
    """

    def __init__(self, config_file: str | None = None):
        """
        Initialize the simulator.

        Args:
            config_file: Path to configuration file (optional)
        """
        self.config = self._load_config(config_file)
        self._setup_logging()
        self._initialize_components()

        # Enhanced features
        self.performance_profiler: Any | None = None
        self.memory_profiler: Any | None = None
        self.visualizer: Any | None = None

        if ENHANCED_FEATURES and self.config.get("simulation", {}).get(
            "enable_profiling", False
        ):
            self.performance_profiler = PerformanceProfiler()
            self.memory_profiler = MemoryProfiler()

        if ENHANCED_FEATURES and self.config.get("simulation", {}).get(
            "enable_visualization", False
        ):
            self.visualizer = PipelineVisualizer()

    def _load_config(self, config_file: str | None = None) -> dict[str, Any]:
        """Load configuration from file or use defaults."""
        default_config = {
            "pipeline": {
                "num_stages": 6,
                "fetch_width": 4,
                "issue_width": 4,
                "execute_units": {
                    "ALU": {"count": 2, "latency": 1},
                    "FPU": {"count": 1, "latency": 3},
                    "LSU": {"count": 1, "latency": 2},
                },
            },
            "branch_predictor": {
                "type": "gshare",
                "num_entries": 1024,
                "history_length": 8,
            },
            "memory": {
                "memory_size": 1048576,
                "instruction_cache": {
                    "size": 32768,
                    "block_size": 64,
                    "associativity": 4,
                },
                "data_cache": {"size": 32768, "block_size": 64, "associativity": 4},
            },
            "simulation": {
                "max_cycles": 10000,
                "output_file": "simulation_results.txt",
                "enable_visualization": False,
                "enable_profiling": False,
            },
            "debug": {"enabled": False, "log_level": "INFO"},
        }

        if config_file and Path(config_file).exists():
            try:
                with open(config_file, encoding="utf-8") as f:
                    file_config = yaml.safe_load(f)
                    # Merge configurations
                    self._deep_update(default_config, file_config)
            except Exception as e:
                print(f"Warning: Could not load config file {config_file}: {e}")
                print("Using default configuration.")

        return default_config

    def _deep_update(self, base_dict: dict, update_dict: dict) -> None:
        """Recursively update a dictionary."""
        for key, value in update_dict.items():
            if (
                key in base_dict
                and isinstance(base_dict[key], dict)
                and isinstance(value, dict)
            ):
                self._deep_update(base_dict[key], value)
            else:
                base_dict[key] = value

    def _setup_logging(self) -> None:
        """Set up logging based on configuration."""
        log_level = getattr(logging, self.config["debug"]["log_level"].upper())
        logging.basicConfig(
            level=log_level,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )
        self.logger = logging.getLogger("simulator")

    def _parse_size(self, size_str: str | int) -> int:
        """Parse size string like '32KB' to integer bytes."""
        if isinstance(size_str, int):
            return size_str

        size_str = str(size_str).upper()
        if size_str.endswith("KB"):
            return int(size_str[:-2]) * 1024
        elif size_str.endswith("MB"):
            return int(size_str[:-2]) * 1024 * 1024
        elif size_str.endswith("GB"):
            return int(size_str[:-2]) * 1024 * 1024 * 1024
        else:
            return int(size_str)

    def _initialize_components(self) -> None:
        """Initialize all simulator components with enhanced features."""
        try:
            # Memory system with enhanced hierarchy
            memory_config = self.config["memory"]
            self.memory = Memory(size=memory_config.get("memory_size", 1048576))

            # Enhanced cache hierarchy
            l1_config = {
                "cache_size": self._parse_size(
                    memory_config["instruction_cache"]["size"]
                ),
                "block_size": memory_config["instruction_cache"]["block_size"],
                "associativity": memory_config["instruction_cache"]["associativity"],
                "hit_latency": 1,
                "miss_penalty": 10,
            }

            self.memory_hierarchy = MemoryHierarchy(l1_config, memory_latency=100)

            # Legacy cache interfaces for compatibility
            icache_config = memory_config["instruction_cache"]
            self.instruction_cache = InstructionCache(
                cache_size=self._parse_size(icache_config["size"]),
                block_size=icache_config["block_size"],
                memory=self.memory,
                fetch_bandwidth=self.config["pipeline"]["fetch_width"],
            )

            dcache_config = memory_config["data_cache"]
            self.data_cache = DataCache(
                cache_size=self._parse_size(dcache_config["size"]),
                block_size=dcache_config["block_size"],
            )

            # Enhanced register file with renaming
            self.register_file = RegisterFile(32)

            # Enhanced register renaming with bandwidth support
            renaming_config = self.config.get("execution", {}).get(
                "register_renaming", {}
            )
            rename_bw = renaming_config.get(
                "rename_bandwidth",
                self.config.get("execution", {}).get("rename_bandwidth", 4),
            )
            commit_bw = renaming_config.get(
                "commit_bandwidth",
                self.config.get("execution", {}).get("commit_bandwidth", 4),
            )
            self.register_renaming = AdvancedRegisterRenaming(
                num_logical_regs=32,
                num_physical_regs=128,
                reorder_buffer_size=64,
                rename_bandwidth=rename_bw,
                commit_bandwidth=commit_bw,
            )

            # Branch predictor
            self.branch_predictor = self._create_branch_predictor()

            # Data forwarding
            self.data_forwarding_unit = DataForwardingUnit()

            # Enhanced hazard controller
            self.hazard_controller = HazardController(self.config["pipeline"])

            # Scoreboard (legacy compatibility)
            self.scoreboard = Scoreboard(32)

            # Enhanced instruction parser
            self.instruction_parser = MIPSInstructionParser()

            # Cycle-accurate execution engine
            self.execution_engine = CycleAccurateExecutionEngine(
                self.register_file,
                self.memory,
                self.data_cache,
                memory_hierarchy=self.memory_hierarchy,
            )

            # Enhanced branch prediction
            predictor_type = self.config.get("branch_predictor", {}).get(
                "type", "tournament"
            )
            if predictor_type == "tournament":
                from branch_prediction.hybrid_predictor import TournamentPredictor

                self.branch_predictor = TournamentPredictor(
                    self.config.get("branch_predictor", {})
                )
            elif predictor_type == "perceptron":
                from branch_prediction.hybrid_predictor import PerceptronPredictor

                self.branch_predictor = PerceptronPredictor(
                    self.config.get("branch_predictor", {})
                )
            elif predictor_type == "adaptive":
                from branch_prediction.hybrid_predictor import (
                    AdaptiveHybridPredictor,
                )

                self.branch_predictor = AdaptiveHybridPredictor(
                    self.config.get("branch_predictor", {})
                )

            # Non-blocking cache support
            if self.config.get("memory", {}).get("non_blocking_cache", False):
                from cache.non_blocking_cache import NonBlockingCache

                cache_config = self.config.get("memory", {}).get("data_cache", {})
                # Convert cache config to proper format
                nb_cache_config = {
                    "cache_size": self._parse_size(cache_config.get("size", "32KB")),
                    "block_size": cache_config.get("block_size", 64),
                    "associativity": cache_config.get("associativity", 4),
                    "hit_latency": cache_config.get("hit_latency", 1),
                    "miss_penalty": cache_config.get("miss_penalty", 10),
                    "mshr_count": cache_config.get("mshr_count", 8),
                    "write_policy": cache_config.get("write_policy", "write_back"),
                }
                self.data_cache = NonBlockingCache(nb_cache_config)  # type: ignore[assignment]

            # Enhanced register renaming
            if self.config.get("execution", {}).get("enhanced_renaming", True):
                from register_file.enhanced_register_renaming import (
                    EnhancedRegisterRenaming,
                )

                renaming_config = self.config.get("execution", {}).get(
                    "register_renaming", {}
                )
                self.register_renaming = EnhancedRegisterRenaming(renaming_config)  # type: ignore[assignment]

            # Power modeling
            if self.config.get("power_modeling", {}).get("enabled", False):
                from profiling.power_model import ProcessorPowerModel

                power_config = self.config.get("power_modeling", {})
                self.power_model: Any = ProcessorPowerModel(power_config)
            else:
                self.power_model = None  # type: ignore[assignment]

            # Pipeline stages
            self._initialize_pipeline_stages()

            self.logger.info("Enhanced simulator components initialized successfully")

        except Exception as e:
            self.logger.error(f"Failed to initialize simulator components: {e}")
            raise

    def _create_branch_predictor(self):
        """Create branch predictor based on configuration."""
        bp_config = self.config["branch_predictor"]
        bp_type = bp_config["type"].lower()

        if bp_type == "always_taken":
            return AlwaysTakenPredictor()
        elif bp_type == "bimodal":
            return BimodalPredictor(num_entries=bp_config["num_entries"])
        elif bp_type == "gshare":
            return GsharePredictor(
                num_entries=bp_config["num_entries"],
                history_length=bp_config["history_length"],
            )
        elif bp_type == "tournament":
            from branch_prediction.hybrid_predictor import TournamentPredictor

            return TournamentPredictor(bp_config)
        elif bp_type == "perceptron":
            from branch_prediction.hybrid_predictor import PerceptronPredictor

            return PerceptronPredictor(bp_config)
        elif bp_type == "adaptive":
            from branch_prediction.hybrid_predictor import AdaptiveHybridPredictor

            return AdaptiveHybridPredictor(bp_config)
        else:
            self.logger.warning(
                f"Unknown branch predictor type: {bp_type}, using always_taken"
            )
            return AlwaysTakenPredictor()

    def _initialize_pipeline_stages(self) -> None:
        """Initialize pipeline stages."""
        pipeline_config = self.config["pipeline"]

        self.fetch_stage = FetchStage(
            instruction_cache=self.instruction_cache,
            branch_predictor=self.branch_predictor,
            memory=self.memory,
        )

        # Count execution units first
        execute_units = pipeline_config["execute_units"]

        # Handle both old and new config formats
        if isinstance(execute_units.get("ALU"), dict):
            alu_count = execute_units.get("ALU", {}).get("count", 2)
            fpu_count = execute_units.get("FPU", {}).get("count", 1)
            lsu_count = execute_units.get("LSU", {}).get("count", 1)
        else:
            # Legacy format
            alu_count = execute_units.get("ALU", 2)
            fpu_count = execute_units.get("FPU", 1)
            lsu_count = execute_units.get("LSU", 1)

        self.decode_stage = DecodeStage(register_file=self.register_file)

        # Process execution units for issue stage
        processed_execute_units = {"ALU": alu_count, "FPU": fpu_count, "LSU": lsu_count}

        self.issue_stage = IssueStage(
            num_reservation_stations=8,  # Default value
            register_file=self.register_file,
            data_forwarding_unit=self.data_forwarding_unit,
            execution_units=processed_execute_units,
        )

        # Use OOO execute stage if configured
        ooo_enabled = self.config.get("execution", {}).get("ooo_execution", False)
        ooo_window_size = self.config.get("execution", {}).get("ooo_window_size", 16)

        if ooo_enabled:
            self.execute_stage: ExecuteStage = OutOfOrderExecuteStage(
                num_alu_units=alu_count,
                num_fpu_units=fpu_count,
                num_lsu_units=lsu_count,
                register_file=self.register_file,
                data_cache=self.data_cache,
                memory=self.memory,
                window_size=ooo_window_size,
            )
            self.logger.info(
                f"OOO execution enabled with window size {ooo_window_size}"
            )
        else:
            self.execute_stage = ExecuteStage(
                num_alu_units=alu_count,
                num_fpu_units=fpu_count,
                num_lsu_units=lsu_count,
                register_file=self.register_file,
                data_cache=self.data_cache,
                memory=self.memory,
            )

        self.memory_access_stage = MemoryAccessStage(
            data_cache=self.data_cache, memory=self.memory
        )

        self.write_back_stage = WriteBackStage(register_file=self.register_file)

    def load_program(self, program_file: str) -> None:
        """
        Load and parse a MIPS assembly program.

        Args:
            program_file: Path to the assembly program file
        """
        try:
            program_path = Path(program_file)
            if not program_path.exists():
                raise FileNotFoundError(f"Program file not found: {program_file}")

            with open(program_path, encoding="utf-8") as f:
                program_content = f.read()

            # Parse assembly program into instructions
            self.parsed_instructions = self.instruction_parser.parse_program(
                program_content
            )

            self.logger.info(f"Loaded and parsed program: {program_file}")
            self.logger.info(f"Program size: {len(program_content)} characters")
            self.logger.info(f"Parsed {len(self.parsed_instructions)} instructions")

            # Load instructions into instruction cache
            for i, instruction in enumerate(self.parsed_instructions):
                address = i * 4
                # Store instruction in cache (simplified)
                self.instruction_cache.add_instruction(address, instruction)  # type: ignore[arg-type]

        except Exception as e:
            self.logger.error(f"Failed to load program {program_file}: {e}")
            raise

    def run_simulation(self) -> dict[str, Any]:
        """
        Run the complete simulation.

        Returns:
            Simulation results and statistics
        """
        try:
            self.logger.info("Starting simulation...")

            # Start profiling if enabled
            if self.performance_profiler:
                self.performance_profiler.start_profiling()

            if self.memory_profiler:
                self.memory_profiler.start_profiling()

            # Main simulation loop
            results = self._run_simulation_loop()

            # Stop profiling and collect results
            if self.performance_profiler:
                profile_result = self.performance_profiler.stop_profiling()
                results["performance_profile"] = {
                    "execution_time": profile_result.execution_time,
                    "cpu_usage": getattr(profile_result, "cpu_usage", {}),
                    "memory_usage": getattr(profile_result, "memory_usage", {}),
                }

            if self.memory_profiler:
                memory_result = self.memory_profiler.stop_profiling()
                results["memory_profile"] = {
                    "memory_growth": getattr(memory_result, "memory_growth", 0),
                    "peak_memory": getattr(memory_result, "peak_memory", 0),
                    "potential_leaks": len(
                        getattr(memory_result, "potential_leaks", [])
                    ),
                    "recommendations": getattr(memory_result, "recommendations", []),
                }

            self.logger.info("Simulation completed successfully")
            return results

        except Exception as e:
            self.logger.error(f"Simulation failed: {e}")
            raise

    def _run_simulation_loop(self) -> dict[str, Any]:
        """
        Enhanced cycle-accurate simulation loop with true superscalar issue.

        Returns:
            Detailed simulation results and statistics
        """
        max_cycles = self.config["simulation"]["max_cycles"]
        issue_width = self.config["pipeline"].get("issue_width", 4)
        cycles = 0
        instructions_completed = 0
        pc = 0
        instruction_id = 0

        self.logger.info(f"Running enhanced simulation for up to {max_cycles} cycles")
        self.logger.info(f"Issue width: {issue_width} instructions/cycle")

        # Initialize performance counters for detailed tracking
        perf_counters = PerformanceCounters()

        # Visualization: feed snapshots periodically
        viz_enabled = self.visualizer is not None
        viz_interval = 10  # Feed snapshot every N cycles

        # Track branch instructions for predictor updates
        branch_instructions: dict[int, Instruction] = {}

        # Track squashed instruction IDs (completed in exec engine but
        # should NOT write results or affect pipeline state)
        squashed_instruction_ids: set[int] = set()

        # Track ROB IDs for register renaming integration
        instruction_rob_ids: dict[int, int] = {}  # instruction_id -> rob_id
        instructions_in_flight = 0  # Track issued instructions still in pipeline

        # Determine which register renaming implementation is active
        # EnhancedRegisterRenaming has 'rob_size'; AdvancedRegisterRenaming does not
        _is_enhanced_renaming = hasattr(self.register_renaming, "rob_size")

        # Enhanced simulation loop with cycle-accurate execution and multi-issue
        total_instructions = len(getattr(self, "parsed_instructions", []))
        program_done = False  # True when all instructions issued or syscall hit
        stall_cycles_count = 0  # Track consecutive cycles with no progress

        while cycles < max_cycles:
            cycles += 1

            # Advance all components by one cycle
            self.execution_engine.current_cycle = cycles
            # NOTE: hazard_controller.advance_cycle() increments current_cycle internally
            self.register_renaming.advance_cycle()
            self.memory_hierarchy.advance_cycle()

            # Advance power model if enabled
            if self.power_model:
                self.power_model.advance_cycle()

            # CRITICAL: Advance hazard controller pipeline stages every cycle
            completed_from_pipeline = self.hazard_controller.advance_cycle()
            for instr_id, instr_state in completed_from_pipeline:
                # Handle register renaming completion for ALL instructions,
                # including squashed ones — otherwise the ROB entry stays
                # non-committable and blocks the ROB head from advancing.
                completed_rob_id = instruction_rob_ids.get(instr_id)
                if completed_rob_id is not None:
                    self.register_renaming.complete_instruction(completed_rob_id, None)

                # Squashed instructions should not count toward completed
                # totals or in-flight tracking (already decremented during flush).
                if instr_id in squashed_instruction_ids:
                    squashed_instruction_ids.discard(instr_id)
                    continue

                instructions_completed += 1

                # Decrement in-flight counter for drain tracking
                instructions_in_flight = max(0, instructions_in_flight - 1)

            # === TRUE SUPERSCALAR: Issue up to issue_width instructions per cycle ===
            instructions_issued_this_cycle = 0
            stall_this_cycle = False

            if not program_done:
                while (
                    instructions_issued_this_cycle < issue_width
                    and pc < total_instructions
                    and not stall_this_cycle
                ):
                    instruction = self.parsed_instructions[pc]

                    # Detect syscall — end of program
                    if instruction.opcode.upper() == "SYSCALL":
                        program_done = True
                        break

                    # Branch prediction: predict when encountering a branch/jump
                    if instruction.instruction_type in [
                        InstructionType.BRANCH,
                        InstructionType.JUMP,
                    ]:
                        try:
                            self.branch_predictor.predict(instruction.address)
                        except Exception:
                            pass
                        # Track for later update
                        branch_instructions[instruction_id] = instruction

                    # Register renaming: attempt to rename before issue
                    rob_id: int | None = None
                    if _is_enhanced_renaming:
                        # EnhancedRegisterRenaming.rename_instruction(instruction) -> int | None
                        try:
                            rob_id = self.register_renaming.rename_instruction(
                                instruction
                            )  # type: ignore[call-arg,arg-type,assignment]
                        except Exception:
                            rob_id = None
                        if rob_id is None:
                            # ROB full or no free physical registers — stall
                            stall_this_cycle = True
                            break
                    else:
                        # AdvancedRegisterRenaming.rename_instruction(id, src_regs, dst_reg)
                        #   -> tuple[bool, list[int], int | None]
                        try:
                            _src_strs = instruction.get_source_registers()
                            _src_regs = [_parse_reg(str(s)) for s in _src_strs]
                            _dst_str = instruction.get_destination_register()
                            _dst_reg = _parse_reg(str(_dst_str)) if _dst_str else None
                            _ok, _renamed_srcs, _renamed_dst = (
                                self.register_renaming.rename_instruction(
                                    instruction_id, _src_regs, _dst_reg
                                )
                            )
                            if not _ok:
                                stall_this_cycle = True
                                break
                            # AdvancedRegisterRenaming tracks by instruction_id
                            rob_id = instruction_id
                        except Exception:
                            rob_id = None

                    # Try to issue instruction through hazard controller
                    if self.hazard_controller.issue_instruction(
                        instruction, instruction_id
                    ):
                        # Start execution in execution engine
                        if self.execution_engine.start_execution(
                            instruction, instruction_id
                        ):
                            # Track ROB ID for this instruction
                            if rob_id is not None:
                                instruction_rob_ids[instruction_id] = rob_id

                            # Record power consumption for instruction execution
                            if self.power_model:
                                functional_unit = (
                                    self._get_functional_unit_for_instruction(
                                        instruction
                                    )
                                )
                                self.power_model.record_instruction_execution(
                                    instruction, functional_unit
                                )

                            pc += 1
                            instruction_id += 1
                            instructions_issued_this_cycle += 1
                            instructions_in_flight += 1
                        else:
                            # Resource contention — squash the ROB entry that
                            # was optimistically allocated by rename.
                            if rob_id is not None and _is_enhanced_renaming:
                                self.register_renaming.squash_renaming(rob_id)  # type: ignore[attr-defined]
                            stall_this_cycle = True
                    else:
                        # Hazard stall — squash the ROB entry that was
                        # optimistically allocated by rename.
                        if rob_id is not None and _is_enhanced_renaming:
                            self.register_renaming.squash_renaming(rob_id)  # type: ignore[attr-defined]
                        stall_this_cycle = True

                # Check if all instructions have been issued
                if pc >= total_instructions:
                    program_done = True

            # Record cycle in performance counters
            in_flight = len(self.execution_engine.executing_instructions)
            perf_counters.record_cycle(
                instructions_issued=instructions_issued_this_cycle,
                instructions_in_flight=in_flight,
            )

            # Advance execution engine
            completed_executions = self.execution_engine.advance_cycle()
            for exec_id, result, data in completed_executions:
                # Complete register renaming for this instruction
                completed_rob_id = instruction_rob_ids.get(exec_id)
                if completed_rob_id is not None:
                    result_val = data if isinstance(data, int) else None
                    self.register_renaming.complete_instruction(
                        completed_rob_id, result_val
                    )

                # Update branch predictor with actual outcome
                if exec_id in branch_instructions:
                    branch_instr = branch_instructions[exec_id]
                    actually_taken = result == ExecutionResult.BRANCH_TAKEN

                    try:
                        self.branch_predictor.update(
                            branch_instr.address, actually_taken
                        )
                    except Exception:
                        pass

                    # Handle branch/jump by updating PC
                    if (
                        actually_taken
                        or branch_instr.instruction_type == InstructionType.JUMP
                    ):
                        if isinstance(data, int):
                            target_pc = (
                                data // 4
                            )  # Convert byte address to instruction index
                            if 0 <= target_pc < total_instructions and target_pc != pc:
                                old_pc = pc
                                pc = target_pc
                                # If jumping backward, allow re-issuing
                                if target_pc <= old_pc:
                                    program_done = False
                                self.logger.debug(
                                    f"Branch/Jump taken, redirecting PC to {pc}"
                                )

                                # --- Pipeline flush on control-flow change ---
                                # Squash all in-flight instructions issued after this branch
                                # (younger instructions have exec_id > exec_id of the branch)
                                squashed_ids = [
                                    eid
                                    for eid in self.execution_engine.executing_instructions
                                    if eid > exec_id
                                ]
                                for eid in squashed_ids:
                                    del self.execution_engine.executing_instructions[
                                        eid
                                    ]
                                    instructions_in_flight = max(
                                        0, instructions_in_flight - 1
                                    )
                                if squashed_ids:
                                    # Also flush from hazard controller to clean up
                                    # register dependencies and stage tracking
                                    self.hazard_controller.flush_instructions(
                                        squashed_ids
                                    )
                                    # Track squashed IDs so we ignore their completions
                                    squashed_instruction_ids.update(squashed_ids)
                                    self.logger.debug(
                                        f"Pipeline flush: squashed {len(squashed_ids)} "
                                        f"younger instructions after branch {exec_id}"
                                    )

                                # Recover register renaming state (RAT checkpoint)
                                branch_rob_id = instruction_rob_ids.get(exec_id)
                                if _is_enhanced_renaming and branch_rob_id is not None:
                                    try:
                                        self.register_renaming.handle_branch_misprediction(
                                            branch_rob_id
                                        )
                                    except Exception:
                                        pass

            # Feed visualization snapshot periodically
            if (
                viz_enabled
                and self.visualizer is not None
                and cycles % viz_interval == 0
            ):
                ipc_now = instructions_completed / cycles if cycles > 0 else 0
                snapshot = PipelineSnapshot(
                    cycle=cycles,
                    fetch=[
                        f"PC={pc}"
                        if pc < len(getattr(self, "parsed_instructions", []))
                        else ""
                    ],
                    decode=[],
                    issue=[],
                    execute=[
                        str(e[0])
                        for e in list(
                            self.execution_engine.executing_instructions.items()
                        )[:4]
                    ],
                    memory=[],
                    writeback=[],
                    branch_prediction_accuracy=self._calculate_branch_accuracy(),
                    ipc=ipc_now,
                    stalls=0,
                    cache_hits=0,
                    cache_misses=0,
                )
                self.visualizer.update(snapshot)

            # Debug output every 100 cycles
            if self.config["debug"]["enabled"] and cycles % 100 == 0:
                self.logger.debug(f"Enhanced simulation cycle: {cycles}")
                self.logger.debug(f"Instructions completed: {instructions_completed}")
                self.logger.debug(f"PC: {pc}")

            # Track progress: if no instructions issued AND none completed, count as stall
            if (
                instructions_issued_this_cycle == 0
                and len(completed_from_pipeline) == 0
            ):
                stall_cycles_count += 1
            else:
                stall_cycles_count = 0

            # Terminate when:
            # 1. Program done AND pipeline fully drained, OR
            # 2. Pipeline stalled with nothing in flight (deadlock / infinite loop detection)
            if program_done and instructions_in_flight == 0:
                self.logger.info("Pipeline fully drained, terminating simulation")
                break
            if stall_cycles_count > 20 and instructions_in_flight == 0:
                self.logger.info(
                    f"No progress for {stall_cycles_count} cycles with empty pipeline, terminating"
                )
                break

        self.logger.info(f"Enhanced simulation terminated after {cycles} cycles")
        self.logger.info(f"Instructions completed: {instructions_completed}")

        # Gather comprehensive statistics
        execution_stats = (
            self.execution_engine.get_statistics()
            if hasattr(self.execution_engine, "get_statistics")
            else {}
        )
        hazard_stats = (
            self.hazard_controller.get_statistics()
            if hasattr(self.hazard_controller, "get_statistics")
            else {}
        )
        renaming_stats = (
            self.register_renaming.get_statistics()
            if hasattr(self.register_renaming, "get_statistics")
            else (
                self.register_renaming.get_stats()
                if hasattr(self.register_renaming, "get_stats")
                else {}
            )
        )
        memory_stats = (
            self.memory_hierarchy.get_statistics()
            if hasattr(self.memory_hierarchy, "get_statistics")
            else {"l1_stats": {"hit_rate": 0.0}}
        )

        # Calculate enhanced performance metrics
        ipc = instructions_completed / cycles if cycles > 0 else 0

        # Calculate pipeline utilization from actual hazard controller stats
        pipeline_utilization = self._calculate_pipeline_utilization(
            hazard_stats, cycles
        )

        # Calculate branch accuracy from actual branch predictor stats
        branch_accuracy = self._calculate_branch_accuracy()

        # Calculate cache hit rate from memory hierarchy stats
        l1_stats = memory_stats.get("l1_stats", {})
        cache_hit_rate = l1_stats.get("hit_rate", 0.0) * 100

        results = {
            "cycles": cycles,
            "instructions": instructions_completed,
            "instructions_completed": instructions_completed,
            "ipc": ipc,
            "issue_width": issue_width,
            "branch_accuracy": branch_accuracy,
            "cache_hit_rate": cache_hit_rate,
            "execution_stats": execution_stats,
            "hazard_stats": hazard_stats,
            "renaming_stats": renaming_stats,
            "memory_stats": memory_stats,
            "pipeline_utilization": pipeline_utilization,
        }

        # Update performance counters with final stats
        perf_counters.update_from_hazard_controller(hazard_stats)
        perf_counters.update_from_execution_engine(execution_stats)
        perf_counters.update_from_memory_hierarchy(memory_stats)
        if hasattr(self, "branch_predictor"):
            perf_counters.update_from_branch_predictor(self.branch_predictor)

        # Add performance counters detailed report to results
        results["performance_counters"] = perf_counters.get_detailed_report()

        # Add power modeling results if enabled
        if self.power_model:
            power_stats = self.power_model.get_comprehensive_stats()
            results.update(
                {
                    "power_stats": power_stats,
                    "energy_per_instruction_pJ": power_stats[
                        "energy_per_instruction_pJ"
                    ],
                    "average_power_mW": power_stats["average_power_mW"],
                    "total_energy_mJ": power_stats["total_energy_mJ"],
                    "processor_temperature_C": power_stats["current_temperature_C"],
                }
            )

        # Add enhanced branch prediction stats
        if hasattr(self.branch_predictor, "get_statistics"):
            results["branch_prediction_stats"] = self.branch_predictor.get_statistics()
        elif hasattr(self.branch_predictor, "get_stats"):
            results["branch_prediction_stats"] = self.branch_predictor.get_stats()

        return results

    def _calculate_branch_accuracy(self) -> float:
        """
        Calculate branch prediction accuracy from actual predictor statistics.

        Returns:
            Branch accuracy as a percentage (0.0-100.0)
        """
        predictor = self.branch_predictor

        # Try multiple interfaces that different predictors expose
        if hasattr(predictor, "get_accuracy"):
            try:
                accuracy = predictor.get_accuracy()
                # get_accuracy() may return 0.0-1.0 or 0.0-100.0
                if 0.0 <= accuracy <= 1.0:
                    return accuracy * 100.0
                return float(accuracy)
            except Exception:
                pass

        if hasattr(predictor, "total_predictions") and hasattr(
            predictor, "total_mispredictions"
        ):
            total = predictor.total_predictions
            if total > 0:
                correct = total - predictor.total_mispredictions
                return (correct / total) * 100.0

        return 0.0

    def _get_functional_unit_for_instruction(self, instruction: Instruction) -> str:
        """Get the functional unit type for an instruction."""
        if instruction.instruction_type == InstructionType.FLOATING_POINT:
            return "FPU_0"
        elif instruction.instruction_type in [
            InstructionType.LOAD,
            InstructionType.STORE,
        ]:
            return "LSU_0"
        else:
            return "ALU_0"

    def _calculate_pipeline_utilization(
        self, hazard_stats: dict, total_cycles: int
    ) -> dict:
        """
        Calculate actual pipeline utilization from hazard controller statistics.

        Args:
            hazard_stats: Statistics from hazard controller
            total_cycles: Total simulation cycles

        Returns:
            Dictionary with utilization percentages for each pipeline stage
        """
        # Get stage occupancy data from hazard controller
        stage_occupancy = hazard_stats.get("stage_occupancy", {})
        # total_stalls = hazard_stats.get("stall_cycles", 0)

        # Calculate utilization for each stage
        # Utilization = (cycles stage was occupied / total cycles) * 100
        pipeline_utilization = {}

        for stage_name in [
            "FETCH",
            "DECODE",
            "ISSUE",
            "EXECUTE",
            "MEMORY",
            "WRITEBACK",
        ]:
            stage_key = stage_name.lower()
            occupied_cycles = stage_occupancy.get(stage_key, 0)

            # Calculate utilization percentage
            if total_cycles > 0:
                utilization = (occupied_cycles / total_cycles) * 100
            else:
                utilization = 0.0

            # Cap at 100%
            utilization = min(utilization, 100.0)

            pipeline_utilization[f"{stage_key}_utilization"] = round(utilization, 2)

        # If no detailed stats available, calculate from instructions completed
        if all(v == 0.0 for v in pipeline_utilization.values()):
            instructions_completed = hazard_stats.get("instructions_completed", 0)

            # Estimate: each instruction spends 1 cycle in each stage (6 stages total)
            # So total stage-cycles = instructions_completed * 6
            # Average utilization per stage = (instructions_completed / total_cycles) * 100
            if total_cycles > 0:
                base_utilization = (instructions_completed / total_cycles) * 100

                # Different stages have different typical utilizations
                pipeline_utilization = {
                    "fetch_utilization": min(
                        base_utilization * 1.1, 100.0
                    ),  # Fetch slightly higher
                    "decode_utilization": min(base_utilization * 1.05, 100.0),
                    "issue_utilization": min(
                        base_utilization * 0.9, 100.0
                    ),  # Issue may stall
                    "execute_utilization": min(base_utilization * 0.95, 100.0),
                    "memory_utilization": min(
                        base_utilization * 0.7, 100.0
                    ),  # Memory less used
                    "writeback_utilization": min(base_utilization * 1.0, 100.0),
                }

                # Round values
                pipeline_utilization = {
                    k: round(v, 2) for k, v in pipeline_utilization.items()
                }

        return pipeline_utilization

    def save_results(self, results: dict[str, Any], output_file: str) -> None:
        """
        Save simulation results to file.

        Args:
            results: Simulation results
            output_file: Output file path
        """
        try:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, "w", encoding="utf-8") as f:
                f.write("Superscalar Pipeline Simulator Results\n")
                f.write("=" * 50 + "\n\n")

                for key, value in results.items():
                    if isinstance(value, dict):
                        f.write(f"{key}:\n")
                        for subkey, subvalue in value.items():
                            f.write(f"  {subkey}: {subvalue}\n")
                    else:
                        f.write(f"{key}: {value}\n")

            self.logger.info(f"Results saved to: {output_path}")

        except Exception as e:
            self.logger.error(f"Failed to save results: {e}")


def create_argument_parser() -> argparse.ArgumentParser:
    """Create and configure argument parser."""
    parser = argparse.ArgumentParser(
        description="Superscalar Pipeline Simulator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --benchmark benchmarks/matrix_multiplication.asm
  %(prog)s --benchmark benchmarks/fibonacci_recursive.asm --visualize
  %(prog)s --config config.yaml --benchmark benchmarks/memory_access_patterns.asm --profile
        """,
    )

    parser.add_argument(
        "--config",
        "-c",
        type=str,
        help="Configuration file path (default: use built-in defaults)",
    )

    parser.add_argument(
        "--benchmark",
        "-b",
        type=str,
        required=True,
        help="Benchmark/program file to simulate",
    )

    parser.add_argument(
        "--output",
        "-o",
        type=str,
        help="Output file for results (default: simulation_results.txt)",
    )

    parser.add_argument(
        "--visualize", action="store_true", help="Enable pipeline visualization"
    )

    parser.add_argument(
        "--profile", action="store_true", help="Enable performance profiling"
    )

    parser.add_argument("--debug", action="store_true", help="Enable debug mode")

    parser.add_argument("--max-cycles", type=int, help="Maximum simulation cycles")

    parser.add_argument("--gui", action="store_true", help="Launch configuration GUI")

    return parser


def main() -> int:
    """Main entry point."""
    parser = create_argument_parser()
    args = parser.parse_args()

    # Launch GUI if requested
    if args.gui:
        if not ENHANCED_FEATURES:
            print(
                "Error: GUI requires enhanced features (tkinter). Install with: pip install -r requirements.txt"
            )
            return 1
        try:
            app = ConfigurationGUI()
            app.run()
            return 0
        except ImportError:
            print("Error: tkinter not available. Install with:")
            print("  Ubuntu/Debian: sudo apt-get install python3-tk")
            print("  macOS: tkinter should be included with Python")
            return 1
        except Exception as e:
            print(f"Error running GUI: {e}")
            return 1

    try:
        # Create simulator
        simulator = SuperscalarSimulator(args.config)

        # Apply command-line overrides
        if args.debug:
            simulator.config["debug"]["enabled"] = True
            simulator.config["debug"]["log_level"] = "DEBUG"
            # Reinitialize logging with debug level
            logging.getLogger().setLevel(logging.DEBUG)

        if args.visualize:
            simulator.config["simulation"]["enable_visualization"] = True

        if args.profile:
            simulator.config["simulation"]["enable_profiling"] = True

        if args.max_cycles:
            simulator.config["simulation"]["max_cycles"] = args.max_cycles

        output_file = args.output or simulator.config["simulation"]["output_file"]

        # Start visualization if enabled
        if simulator.visualizer:
            simulator.visualizer.start()

        # Load and run program
        simulator.load_program(args.benchmark)
        results = simulator.run_simulation()

        # Stop visualization and show dashboard if enabled
        if simulator.visualizer:
            simulator.visualizer.stop()
            try:
                create_performance_dashboard(results)
            except Exception:
                pass  # Dashboard is optional, don't fail on display issues

        # Save results
        simulator.save_results(results, output_file)

        # Print summary
        print("\nSimulation Summary:")
        print(f"  Cycles: {results['cycles']}")
        print(f"  Instructions: {results['instructions']}")
        print(f"  IPC: {results['ipc']:.3f}")
        print(f"  Branch Accuracy: {results['branch_accuracy']:.1f}%")
        print(f"  Cache Hit Rate: {results['cache_hit_rate']:.1f}%")
        print(f"\nResults saved to: {output_file}")

        return 0

    except KeyboardInterrupt:
        print("\nSimulation interrupted by user")
        return 1
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        if args.debug:
            import traceback

            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
