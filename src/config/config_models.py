"""
Pydantic models for configuration validation and type checking.

This module defines the configuration schema for the simulator with
comprehensive validation rules and default values.
"""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


class BranchPredictorType(str, Enum):
    """Supported branch predictor types."""
    ALWAYS_TAKEN = "always_taken"
    BIMODAL = "bimodal"
    GSHARE = "gshare"


class LogLevel(str, Enum):
    """Supported logging levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class ExecutionUnitConfig(BaseModel):
    """Configuration for execution units."""
    count: int = Field(default=1, ge=1, le=8, description="Number of units")
    latency: int = Field(default=1, ge=1, le=10, description="Execution latency in cycles")


class PipelineConfig(BaseModel):
    """Pipeline configuration with validation."""
    
    num_stages: int = Field(
        default=6,
        ge=3,
        le=10,
        description="Number of pipeline stages"
    )
    
    fetch_width: int = Field(
        default=4,
        ge=1,
        le=8,
        description="Instructions fetched per cycle"
    )
    
    issue_width: int = Field(
        default=4,
        ge=1,
        le=8,
        description="Instructions issued per cycle"
    )
    
    execute_units: dict[str, ExecutionUnitConfig] = Field(
        default_factory=lambda: {
            "ALU": ExecutionUnitConfig(count=2, latency=1),
            "FPU": ExecutionUnitConfig(count=1, latency=3),
            "LSU": ExecutionUnitConfig(count=1, latency=2),
        },
        description="Execution unit configuration"
    )
    
    @field_validator('execute_units')
    @classmethod
    def validate_execution_units(cls, v: dict[str, Any]) -> dict[str, ExecutionUnitConfig]:
        """Validate and convert execution unit configurations."""
        result = {}
        for name, config in v.items():
            if isinstance(config, dict):
                result[name] = ExecutionUnitConfig(**config)
            elif isinstance(config, ExecutionUnitConfig):
                result[name] = config
            else:
                raise ValueError(f"Invalid execution unit config for {name}")
        return result


class BranchPredictorConfig(BaseModel):
    """Branch predictor configuration."""
    
    type: BranchPredictorType = Field(
        default=BranchPredictorType.GSHARE,
        description="Branch predictor algorithm"
    )
    
    num_entries: int = Field(
        default=1024,
        ge=64,
        le=65536,
        description="Number of predictor entries"
    )
    
    history_length: int = Field(
        default=8,
        ge=1,
        le=16,
        description="Global history length (for gshare)"
    )
    
    @model_validator(mode='after')
    def validate_predictor_config(self) -> BranchPredictorConfig:
        """Validate predictor-specific configuration."""
        if self.type == BranchPredictorType.GSHARE:
            if self.history_length > 12:
                raise ValueError("History length should be <= 12 for gshare predictor")
        return self


class CacheConfig(BaseModel):
    """Cache configuration."""
    
    size: int = Field(
        default=32768,
        ge=1024,
        le=1048576,
        description="Cache size in bytes"
    )
    
    block_size: int = Field(
        default=64,
        ge=16,
        le=256,
        description="Cache block size in bytes"
    )
    
    associativity: int = Field(
        default=4,
        ge=1,
        le=16,
        description="Cache associativity (1 = direct mapped)"
    )
    
    @field_validator('block_size')
    @classmethod
    def validate_block_size(cls, v: int) -> int:
        """Validate block size is power of 2."""
        if v & (v - 1) != 0:
            raise ValueError("Block size must be a power of 2")
        return v
    
    @field_validator('size')
    @classmethod
    def validate_cache_size(cls, v: int) -> int:
        """Validate cache size is reasonable."""
        if v < 1024:
            raise ValueError("Cache size must be at least 1KB")
        return v


class MemoryConfig(BaseModel):
    """Memory system configuration."""
    
    memory_size: int = Field(
        default=1048576,
        ge=65536,
        le=134217728,
        description="Main memory size in bytes"
    )
    
    instruction_cache: CacheConfig = Field(
        default_factory=lambda: CacheConfig(size=32768, block_size=64, associativity=4),
        description="Instruction cache configuration"
    )
    
    data_cache: CacheConfig = Field(
        default_factory=lambda: CacheConfig(size=32768, block_size=64, associativity=4),
        description="Data cache configuration"
    )


class SimulationConfig(BaseModel):
    """Simulation execution configuration."""
    
    max_cycles: int = Field(
        default=10000,
        ge=100,
        le=10000000,
        description="Maximum simulation cycles"
    )
    
    output_file: Optional[str] = Field(
        default="simulation_results.txt",
        description="Output file for results"
    )
    
    enable_visualization: bool = Field(
        default=False,
        description="Enable pipeline visualization"
    )
    
    enable_profiling: bool = Field(
        default=True,
        description="Enable performance profiling"
    )
    
    enable_statistics: bool = Field(
        default=True,
        description="Enable detailed statistics collection"
    )


class DebugConfig(BaseModel):
    """Debug and logging configuration."""
    
    enabled: bool = Field(
        default=False,
        description="Enable debug mode"
    )
    
    log_level: LogLevel = Field(
        default=LogLevel.INFO,
        description="Logging level"
    )
    
    log_file: Optional[str] = Field(
        default=None,
        description="Log file path (None for console only)"
    )
    
    trace_instructions: bool = Field(
        default=False,
        description="Enable instruction tracing"
    )
    
    trace_pipeline: bool = Field(
        default=False,
        description="Enable pipeline stage tracing"
    )


class SimulatorConfig(BaseModel):
    """Complete simulator configuration."""
    
    pipeline: PipelineConfig = Field(
        default_factory=PipelineConfig,
        description="Pipeline configuration"
    )
    
    branch_predictor: BranchPredictorConfig = Field(
        default_factory=BranchPredictorConfig,
        description="Branch predictor configuration"
    )
    
    memory: MemoryConfig = Field(
        default_factory=MemoryConfig,
        description="Memory system configuration"
    )
    
    simulation: SimulationConfig = Field(
        default_factory=SimulationConfig,
        description="Simulation configuration"
    )
    
    debug: DebugConfig = Field(
        default_factory=DebugConfig,
        description="Debug configuration"
    )
    
    @model_validator(mode='after')
    def validate_config_consistency(self) -> SimulatorConfig:
        """Validate configuration consistency across components."""
        # Ensure issue width doesn't exceed fetch width
        if self.pipeline.issue_width > self.pipeline.fetch_width:
            raise ValueError("Issue width cannot exceed fetch width")
        
        # Ensure reasonable cache sizes relative to memory
        total_cache_size = (
            self.memory.instruction_cache.size +
            self.memory.data_cache.size
        )
        if total_cache_size > self.memory.memory_size // 4:
            raise ValueError("Total cache size should not exceed 25% of memory size")
        
        return self
    
    def model_dump_yaml(self) -> str:
        """Export configuration as YAML string."""
        import yaml
        return yaml.dump(
            self.model_dump(exclude_none=True),
            default_flow_style=False,
            sort_keys=False
        )
    
    def save_to_file(self, file_path: str | Path) -> None:
        """Save configuration to YAML file."""
        import yaml
        
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert to dict with proper enum serialization
        config_dict = self.model_dump(mode='python')
        
        # Convert enums to their string values
        def convert_enums(obj):
            if isinstance(obj, dict):
                return {k: convert_enums(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_enums(item) for item in obj]
            elif hasattr(obj, 'value'):  # Enum
                return obj.value
            else:
                return obj
        
        config_dict = convert_enums(config_dict)
        
        with open(path, 'w', encoding='utf-8') as f:
            yaml.dump(config_dict, f, default_flow_style=False, sort_keys=False)
