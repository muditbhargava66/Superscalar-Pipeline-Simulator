# API Reference

This document provides comprehensive API documentation for the Superscalar Pipeline Simulator. The API is organized by modules and includes detailed information about classes, methods, and usage patterns.

## Core Modules

### Configuration Management

#### `config.config_manager.ConfigManager`

Manages simulator configuration with validation and environment variable support.

```python
from config.config_manager import ConfigManager

config_manager = ConfigManager()
```

**Methods:**

- `get_default_config() -> dict`: Returns default configuration
- `load_config(file_path: str = None) -> dict`: Loads configuration from file
- `validate_config(config: dict) -> dict`: Validates configuration parameters
- `save_config(config: dict, file_path: str) -> None`: Saves configuration to file

**Example:**
```python
config_manager = ConfigManager()
config = config_manager.load_config('custom_config.yaml')
validated_config = config_manager.validate_config(config)
```

#### `config.config_models.SimulatorConfig`

Pydantic model for type-safe configuration validation.

```python
from config.config_models import SimulatorConfig

# Load configuration from YAML file
from config.config_manager import ConfigManager
config_manager = ConfigManager()
config = config_manager.load_config('config.yaml')

# Or build configuration programmatically
config = {
    'pipeline': {
        'num_stages': 6,
        'fetch_width': 8,
        'issue_width': 6,
    },
    'memory': {
        'instruction_cache': {'size': '32KB', 'block_size': 64, 'associativity': 4},
        'data_cache': {'size': '32KB', 'block_size': 64, 'associativity': 4},
    },
}
```

### Instruction Processing

#### `utils.instruction.Instruction`

Represents a single processor instruction with metadata.

```python
from utils.instruction import Instruction, InstructionType

instruction = Instruction(
    address=0x1000,
    opcode="ADD",
    operands=["$t0", "$t1", "$t2"],
    instruction_type=InstructionType.ARITHMETIC
)
```

**Attributes:**
- `address: int`: Instruction address
- `opcode: str`: Operation code
- `operands: list[str]`: Instruction operands
- `instruction_type: InstructionType`: Type classification
- `cycle_issued: int`: Cycle when issued
- `cycle_completed: int`: Cycle when completed

**Methods:**
- `is_memory_operation() -> bool`: Check if memory operation
- `is_branch_operation() -> bool`: Check if branch operation
- `get_source_registers() -> list[str]`: Get source register names
- `get_destination_register() -> str`: Get destination register name

#### `utils.instruction_parser.MIPSInstructionParser`

Parses MIPS assembly code into instruction objects.

```python
from utils.instruction_parser import MIPSInstructionParser

parser = MIPSInstructionParser()
instructions = parser.parse_program(assembly_code)
```

**Methods:**
- `parse_program(code: str) -> list[Instruction]`: Parse assembly code
- `parse_instruction(line: str, address: int) -> Instruction`: Parse single instruction
- `validate_syntax(code: str) -> bool`: Validate assembly syntax

### Branch Prediction

#### `branch_prediction.base_predictor.BranchPredictor`

Abstract base class for all branch predictors.

```python
from branch_prediction.base_predictor import BranchPredictor, PredictionResult

class CustomPredictor(BranchPredictor):
    def predict(self, pc: int) -> PredictionResult:
        # Implementation
        pass

    def update(self, pc: int, taken: bool) -> None:
        # Implementation
        pass
```

#### `branch_prediction.hybrid_predictor.TournamentPredictor`

Tournament predictor combining multiple prediction mechanisms.

```python
from branch_prediction.hybrid_predictor import TournamentPredictor

config = {
    'predictor_1': {'size': 1024},
    'predictor_2': {'size': 1024},
    'meta_bits': 10
}
predictor = TournamentPredictor(config)

# Make prediction
result = predictor.predict(pc=0x1000)
print(f"Predicted: {result.taken}, Confidence: {result.confidence}")

# Update with actual outcome
predictor.update(pc=0x1000, taken=True)
```

#### `branch_prediction.hybrid_predictor.PerceptronPredictor`

Neural perceptron-based branch predictor.

```python
from branch_prediction.hybrid_predictor import PerceptronPredictor

config = {
    'history_length': 8,
    'table_size': 256,
    'threshold': 1.93
}
predictor = PerceptronPredictor(config)
```

### Cache System

#### `cache.enhanced_cache.EnhancedCache`

Advanced cache implementation with detailed timing and statistics.

```python
from cache.enhanced_cache import EnhancedCache, MemoryAccessType

config = {
    'cache_size': 32768,
    'block_size': 64,
    'associativity': 4,
    'hit_latency': 1,
    'miss_penalty': 10,
}
cache = EnhancedCache(config)

# Access cache
result = cache.access(
    address=0x1000,
    access_type=MemoryAccessType.READ
)
```

**Methods:**

- `access(address: int, access_type: MemoryAccessType) -> tuple`: Access cache, returns hit status, latency, and data
- `advance_cycle() -> list`: Advance one cycle, returns completed memory requests
- `get_statistics() -> dict`: Get cache statistics including hit rate, miss rate, and access counts
- `reset_stats() -> None`: Reset statistics

#### `cache.enhanced_cache.MemoryHierarchy`

Multi-level memory hierarchy with L1, L2, and main memory integration.

```python
from cache.enhanced_cache import MemoryHierarchy

l1_config = {
    'cache_size': 32768,
    'block_size': 64,
    'associativity': 4,
    'hit_latency': 1,
    'miss_penalty': 10,
}
hierarchy = MemoryHierarchy(l1_config, memory_latency=100)

# Advance cycle and get statistics
hierarchy.advance_cycle()
stats = hierarchy.get_statistics()
```

**Methods:**

- `access(address: int, access_type: str, data: int = 0) -> tuple`: Access through hierarchy
- `advance_cycle() -> None`: Advance one cycle for pending requests
- `get_statistics() -> dict`: Get hierarchy-wide statistics including L1/L2 hit rates

#### `cache.non_blocking_cache.NonBlockingCache`

Non-blocking cache with MSHR (Miss Status Holding Register) support.

```python
from cache.non_blocking_cache import NonBlockingCache

config = {
    'size': 32768,
    'block_size': 64,
    'associativity': 4,
    'mshr_count': 8
}
cache = NonBlockingCache(config)

# Non-blocking access
hit, latency, data = cache.access(0x1000, 'READ')
if not hit:
    # MSHR allocated for outstanding miss
    outstanding_misses = cache.get_outstanding_misses()
```

### Register Management

#### `register_file.enhanced_register_renaming.EnhancedRegisterRenaming`

Advanced register renaming with reorder buffer and precise exceptions.

```python
from register_file.enhanced_register_renaming import EnhancedRegisterRenaming

config = {
    'architectural_registers': 32,
    'physical_registers': 128,
    'rob_size': 64,
    'issue_queue_size': 32
}
renamer = EnhancedRegisterRenaming(config)

# Rename instruction
rob_id = renamer.rename_instruction(instruction)

# Issue instructions
issued = renamer.issue_instructions(cycle=10)

# Complete instruction
renamer.complete_instruction(rob_id, cycle=15, result=42)

# Commit instructions
committed = renamer.commit_instructions(cycle=20)
```

**Methods:**
- `rename_instruction(instruction: Instruction) -> int`: Rename instruction registers
- `issue_instructions(cycle: int) -> list[tuple[int, str]]`: Issue ready instructions
- `complete_instruction(rob_id: int, cycle: int, result: Any) -> bool`: Mark instruction complete
- `commit_instructions(cycle: int) -> list[int]`: Commit completed instructions
- `handle_branch_misprediction(rob_id: int) -> None`: Handle misprediction recovery

### Power Modeling

#### `profiling.power_model.ProcessorPowerModel`

Comprehensive processor power and energy modeling.

```python
from profiling.power_model import ProcessorPowerModel
from utils.instruction import InstructionType

config = {
    'technology_nm': 45.0,
    'voltage_v': 1.0,
    'frequency_ghz': 2.5,
    'temperature_c': 25.0
}
power_model = ProcessorPowerModel(config)

# Record activity
power_model.record_activity(
    cycle=10,
    instruction_type=InstructionType.ARITHMETIC,
    unit='ALU_0'
)

# Get power metrics
total_energy = power_model.get_total_energy()
avg_power = power_model.get_average_power()
energy_per_instr = power_model.get_energy_per_instruction()
power_efficiency = power_model.get_power_efficiency()
```

**Methods:**
- `record_activity(cycle: int, instruction_type: InstructionType, unit: str) -> None`: Record execution activity
- `get_total_energy() -> float`: Get total energy consumption (mJ)
- `get_average_power() -> float`: Get average power consumption (mW)
- `get_energy_per_instruction() -> float`: Get energy per instruction (pJ)
- `get_power_efficiency() -> float`: Get power efficiency (MIPS/W)
- `get_power_breakdown() -> dict[str, float]`: Get power breakdown by component

### Performance Profiling

#### `profiling.performance_profiler.PerformanceProfiler`

Real-time performance monitoring and bottleneck analysis.

```python
from profiling.performance_profiler import PerformanceProfiler

profiler = PerformanceProfiler()
profiler.start_profiling()

# Simulate execution
profiler.record_instruction_execution('ADD', InstructionType.ARITHMETIC, latency=1)
profiler.record_pipeline_stall('issue', cycles=3)

profiler.stop_profiling()

# Get results
metrics = profiler.get_performance_metrics()
bottlenecks = profiler.identify_bottlenecks()
recommendations = profiler.get_optimization_recommendations()
```

#### `profiling.memory_profiler.MemoryProfiler`

Memory usage tracking and leak detection.

```python
from profiling.memory_profiler import MemoryProfiler

memory_profiler = MemoryProfiler()
memory_profiler.start_monitoring()

# Simulate memory allocations
# ... simulation code ...

stats = memory_profiler.get_memory_stats()
leaks = memory_profiler.detect_leaks()
memory_profiler.stop_monitoring()
```

### Exception Handling

#### `exceptions.simulator_exceptions`

Comprehensive exception hierarchy for error handling.

```python
from exceptions.simulator_exceptions import (
    SimulatorError, ConfigurationError, InstructionError,
    PipelineStallError, CacheError, ExecutionError,
    MemoryAccessError, handle_simulator_error, create_error_context,
)

try:
    # Simulation code
    pass
except ConfigurationError as e:
    print(f"Configuration error: {e}")
    print(f"Details: {e.details}")
except InstructionError as e:
    print(f"Instruction error: {e.instruction}")
except PipelineStallError as e:
    print(f"Pipeline stall: {e.stall_reason}")
except SimulatorError as e:
    print(f"Simulator error: {e}")
```

**Exception Types:**
- `SimulatorError`: Base exception class for all simulator errors
- `ConfigurationError`: Configuration validation errors
- `InstructionError`: Assembly parsing and instruction format errors
- `PipelineError`: Base class for pipeline-related errors (with stage and cycle info)
- `PipelineStallError`: Pipeline stall conditions (with stall reason)
- `HazardError`: Unresolvable data/control/structural hazards
- `CacheError`: Cache-related errors (with cache type info)
- `ExecutionError`: Instruction execution errors (with unit type and operation)
- `MemoryError`: Base class for memory system errors
- `MemoryAccessError`: Memory access violations (with address and access type)
- `BranchPredictionError`: Branch predictor errors
- `RegisterFileError`: Register file errors
- `ValidationError`: Input validation and state validation failures

### Performance Counters

#### `performance.performance_counters.PerformanceCounters`

Detailed performance counters for pipeline analysis.

```python
from performance.performance_counters import PerformanceCounters

counters = PerformanceCounters()

# Record cycle activity
counters.record_cycle(instructions_issued=2, instructions_in_flight=5)

# Update from component statistics
counters.update_from_hazard_controller(hazard_stats)
counters.update_from_execution_engine(exec_stats)
counters.update_from_memory_hierarchy(memory_stats)
counters.update_from_branch_predictor(predictor)

# Get comprehensive report
report = counters.get_detailed_report()
```

**Methods:**

- `record_cycle(instructions_issued: int, instructions_in_flight: int) -> None`: Record per-cycle activity
- `update_from_hazard_controller(stats: dict) -> None`: Import hazard controller statistics
- `update_from_execution_engine(stats: dict) -> None`: Import execution engine statistics
- `update_from_memory_hierarchy(stats: dict) -> None`: Import memory hierarchy statistics
- `update_from_branch_predictor(predictor) -> None`: Import branch predictor statistics
- `get_detailed_report() -> dict`: Get comprehensive performance report

## Usage Patterns

### Basic Simulation Setup

```python
from config.config_manager import ConfigManager
from utils.instruction_parser import MIPSInstructionParser
from profiling.performance_profiler import PerformanceProfiler

# Load configuration
config_manager = ConfigManager()
config = config_manager.load_config('config.yaml')

# Parse assembly code
parser = MIPSInstructionParser()
instructions = parser.parse_program(assembly_code)

# Setup profiling
profiler = PerformanceProfiler()
profiler.start_profiling()

# Run simulation
# ... simulation logic ...

# Get results
metrics = profiler.get_performance_metrics()
```

### Advanced Configuration

```python
from config.config_manager import ConfigManager

# Load and customize configuration
config_manager = ConfigManager()
config = config_manager.load_config('config.yaml')

# Override specific settings
config['pipeline']['issue_width'] = 6
config['execution']['rename_bandwidth'] = 8
config['branch_predictor']['type'] = 'tournament'
config['simulation']['max_cycles'] = 50000

# Use with simulator
simulator = SuperscalarSimulator('config.yaml')
```

### Performance Analysis

```python
from profiling.benchmark_runner import BenchmarkRunner
from profiling.performance_profiler import PerformanceProfiler

# Run benchmark suite
runner = BenchmarkRunner()
results = runner.run_benchmark_suite([
    'benchmarks/matrix_multiplication.asm',
    'benchmarks/bubble_sort.asm',
    'benchmarks/fibonacci_recursive.asm'
])

# Analyze results
for benchmark, result in results.items():
    print(f"{benchmark}: IPC={result['ipc']:.2f}, "
          f"Energy={result['energy']:.3f}mJ")
```

### Error Handling Best Practices

```python
from exceptions.simulator_exceptions import SimulatorError, handle_simulator_error
import logging

logger = logging.getLogger(__name__)

try:
    # Simulation code
    simulator.run_simulation()
except SimulatorError as e:
    error_info = handle_simulator_error(e, logger)

    # Log structured error information
    logger.error(f"Simulation failed: {error_info['message']}")
    logger.debug(f"Error details: {error_info['details']}")

    # Take appropriate action based on error type
    if error_info['details'].get('recoverable'):
        # Attempt recovery
        pass
    else:
        # Terminate gracefully
        raise
```

## Type Hints and Annotations

The simulator uses comprehensive type hints for better code quality and IDE support:

```python
from typing import Optional, Union
from utils.instruction import Instruction

def process_instructions(
    instructions: list[Instruction],
    config: dict[str, Any],
    max_cycles: Optional[int] = None
) -> dict[str, Union[int, float]]:
    """Process instructions and return performance metrics."""
    # Implementation
    pass
```

## Logging and Debugging

```python
import logging
from config.config_manager import ConfigManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Enable debug mode
config = ConfigManager().load_config()
config['debug']['enabled'] = True
config['debug']['log_level'] = 'DEBUG'
```

## Testing Support

### Test Fixtures

```python
import pytest
from unittest.mock import Mock, patch

# Test fixtures
@pytest.fixture
def sample_config():
    return {
        'pipeline': {'width': 4, 'depth': 5},
        'cache': {'l1d_size': 32, 'block_size': 64}
    }

@pytest.fixture
def sample_instructions():
    from utils.instruction import Instruction
    return [
        Instruction(0x1000, "ADD", ["$t0", "$t1", "$t2"]),
        Instruction(0x1004, "LW", ["$t3", "0($sp)"]),
    ]

# Test example
def test_instruction_parsing(sample_instructions):
    from utils.instruction_parser import MIPSInstructionParser
    parser = MIPSInstructionParser()
    result = parser.parse_program("add $t0, $t1, $t2")
    assert len(result) == 1
    assert result[0].opcode == "ADD"
```

### Running Tests

```bash
# Run all tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ -v --cov=src

# Run specific test file
python -m pytest tests/test_pipeline_stages.py -v

# Run specific test class
python -m pytest tests/test_pipeline_stages.py::TestFetchStage -v
```

This API reference provides the foundation for using the simulator programmatically. For more detailed examples, see the `examples/` directory and the user guide.
