#!/usr/bin/env python3
"""
Configuration Management Example

This example demonstrates how to use the configuration management system
to customize simulator behavior and validate configuration parameters.
Includes v1.2.0 enhanced execution options (rename/commit bandwidth, OOO).
"""

import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from config.config_manager import ConfigManager
from config.config_models import SimulatorConfig
from exceptions.simulator_exceptions import ConfigurationError


def demonstrate_default_configuration():
    """Show the default configuration structure."""
    print("Default Configuration")
    print("-" * 30)

    config_manager = ConfigManager()
    default_config = config_manager.load_default()

    print("Pipeline Configuration:")
    pipeline_config = default_config.pipeline
    print(f"   Width: {getattr(pipeline_config, 'fetch_width', 4)} instructions")
    print(f"   Depth: {getattr(pipeline_config, 'num_stages', 5)} stages")
    print(f"   Fetch Width: {getattr(pipeline_config, 'fetch_width', 4)}")
    print(f"   Issue Width: {getattr(pipeline_config, 'issue_width', 4)}")

    print("\nMemory Configuration:")
    memory_config = default_config.memory
    print(
        f"   L1 Instruction Size: {getattr(memory_config.instruction_cache, 'size', 32768) // 1024} KB"
    )
    print(
        f"   L1 Data Size: {getattr(memory_config.data_cache, 'size', 32768) // 1024} KB"
    )
    print(f"   Block Size: {getattr(memory_config.data_cache, 'block_size', 64)} bytes")
    print(f"   Associativity: {getattr(memory_config.data_cache, 'associativity', 4)}")

    print("\nBranch Predictor Configuration:")
    bp_config = default_config.branch_predictor
    print(f"   Type: {getattr(bp_config, 'type', 'gshare')}")
    print(f"   Size: {getattr(bp_config, 'num_entries', 1024)} entries")
    print(f"   History Length: {getattr(bp_config, 'history_length', 8)}")

    print("\nExecution Units:")
    pipeline_config = default_config.pipeline
    print(
        f"   ALU Count: {getattr(pipeline_config.execute_units.get('ALU', {}), 'count', 2)}"
    )
    print(
        f"   FPU Count: {getattr(pipeline_config.execute_units.get('FPU', {}), 'count', 1)}"
    )
    print(
        f"   LSU Count: {getattr(pipeline_config.execute_units.get('LSU', {}), 'count', 1)}"
    )


def demonstrate_custom_configuration():
    """Show how to create and validate custom configurations."""
    print("\nCustom Configuration")
    print("-" * 30)

    # Create custom configuration
    custom_config = {
        "pipeline": {
            "width": 8,
            "depth": 7,
            "fetch_width": 8,
            "issue_width": 6,
        },
        "memory": {
            "memory_size": 2097152,
            "instruction_cache": {"size": 65536, "block_size": 64, "associativity": 4},
            "data_cache": {"size": 65536, "block_size": 64, "associativity": 8},
        },
        "branch_predictor": {
            "type": "gshare",
            "num_entries": 2048,
            "history_length": 10,
        },
    }

    print("Custom High-Performance Configuration:")
    print(f"   Pipeline Width: {custom_config['pipeline']['width']} instructions")
    print(f"   Memory Size: {custom_config['memory']['memory_size'] // 1024} KB")
    print(f"   Branch Predictor: {custom_config['branch_predictor']['type']}")
    print(f"   Data Cache: {custom_config['memory']['data_cache']['size'] // 1024} KB")

    # Create configuration from dictionary
    config_manager = ConfigManager()
    try:
        validated_config = config_manager.create_from_dict(custom_config)
        print("   Configuration validation: PASSED")

        # Show effective configuration
        print("\nEffective Configuration (after validation):")
        print(f"   Pipeline Fetch Width: {validated_config.pipeline.fetch_width}")
        print(f"   Memory Size: {validated_config.memory.memory_size // 1024} KB")
        print(f"   Data Cache: {validated_config.memory.data_cache.size // 1024} KB")

    except Exception as e:
        print(f"   Configuration validation: FAILED - {e}")


def demonstrate_environment_overrides():
    """Show how environment variables can override configuration."""
    print("\nEnvironment Variable Overrides")
    print("-" * 30)

    # Set some environment variables (simulation)
    os.environ["SIMULATOR_PIPELINE_WIDTH"] = "6"
    os.environ["SIMULATOR_CACHE_L1D_SIZE"] = "48"
    os.environ["SIMULATOR_BRANCH_PREDICTOR_TYPE"] = "gshare"

    config_manager = ConfigManager()
    config = config_manager.load_default()

    print("Environment variables set:")
    print("   SIMULATOR_PIPELINE_WIDTH=6")
    print("   SIMULATOR_CACHE_L1D_SIZE=48")
    print("   SIMULATOR_BRANCH_PREDICTOR_TYPE=gshare")

    print("\nResulting configuration:")
    print(f"   Pipeline Width: {getattr(config.pipeline, 'fetch_width', 'default')}")
    print(
        f"   L1D Cache Size: {getattr(config.memory.data_cache, 'size', 32768) // 1024} KB"
    )
    print(f"   Branch Predictor: {getattr(config.branch_predictor, 'type', 'default')}")

    # Clean up environment variables
    for key in [
        "SIMULATOR_PIPELINE_WIDTH",
        "SIMULATOR_CACHE_L1D_SIZE",
        "SIMULATOR_BRANCH_PREDICTOR_TYPE",
    ]:
        if key in os.environ:
            del os.environ[key]


def demonstrate_configuration_profiles():
    """Show predefined configuration profiles for different use cases."""
    print("\nConfiguration Profiles")
    print("-" * 30)

    profiles = {
        "low_power": {
            "pipeline": {"width": 2, "depth": 5},
            "cache": {"l1d_size": 16, "l2_size": 128},
            "execution_units": {"alu_count": 1, "fpu_count": 1},
            "frequency_ghz": 1.0,
            "voltage_v": 0.8,
        },
        "high_performance": {
            "pipeline": {"width": 8, "depth": 7},
            "cache": {"l1d_size": 64, "l2_size": 1024},
            "execution_units": {"alu_count": 4, "fpu_count": 2},
            "frequency_ghz": 3.5,
            "voltage_v": 1.2,
        },
        "research": {
            "pipeline": {"width": 6, "depth": 8},
            "cache": {"l1d_size": 32, "l2_size": 512},
            "branch_predictor": {"type": "tournament", "size": 4096},
            "register_file": {"physical_registers": 512},
            "frequency_ghz": 2.5,
        },
    }

    for profile_name, profile_config in profiles.items():
        print(f"\n{profile_name.replace('_', ' ').title()} Profile:")

        pipeline = profile_config.get("pipeline", {})
        cache = profile_config.get("cache", {})
        units = profile_config.get("execution_units", {})

        print(
            f"   Pipeline: {pipeline.get('width', 'default')} wide, {pipeline.get('depth', 'default')} deep"
        )
        print(
            f"   Cache: L1D {cache.get('l1d_size', 'default')} KB, L2 {cache.get('l2_size', 'default')} KB"
        )
        print(
            f"   Units: {units.get('alu_count', 'default')} ALU, {units.get('fpu_count', 'default')} FPU"
        )

        if "frequency_ghz" in profile_config:
            print(f"   Frequency: {profile_config['frequency_ghz']} GHz")
        if "voltage_v" in profile_config:
            print(f"   Voltage: {profile_config['voltage_v']} V")


def demonstrate_configuration_validation():
    """Show configuration validation and error handling."""
    print("\nConfiguration Validation")
    print("-" * 30)

    config_manager = ConfigManager()

    # Test valid configuration
    valid_config = {
        "pipeline": {"fetch_width": 4, "num_stages": 5},
        "memory": {"data_cache": {"size": 32768, "block_size": 64}},
    }

    try:
        config_manager.create_from_dict(valid_config)
        print("Valid configuration: PASSED")
    except Exception as e:
        print(f"Valid configuration: FAILED - {e}")

    # Test invalid configurations
    invalid_configs = [
        {
            "pipeline": {"fetch_width": 0},  # Invalid width
            "description": "Zero pipeline width",
        },
        {
            "memory": {"data_cache": {"block_size": 33}},  # Non-power-of-2 block size
            "description": "Invalid block size",
        },
        {
            "pipeline": {"execute_units": {"ALU": {"count": -1}}},  # Negative count
            "description": "Negative ALU count",
        },
    ]

    for invalid_config in invalid_configs:
        config_data = {k: v for k, v in invalid_config.items() if k != "description"}
        try:
            config_manager.create_from_dict(config_data)
            print(f"{invalid_config['description']}: UNEXPECTEDLY PASSED")
        except Exception as e:
            print(
                f"{invalid_config['description']}: CORRECTLY REJECTED - {str(e)[:50]}..."
            )


def demonstrate_enhanced_execution_config():
    """Show v1.2.0 enhanced execution configuration options."""
    print("\nEnhanced Execution Configuration (v1.2.0)")
    print("-" * 30)

    import yaml

    config_path = Path(__file__).parent.parent / "config.yaml"
    with open(config_path, encoding="utf-8") as f:
        config = yaml.safe_load(f)

    execution = config.get("execution", {})

    print("Execution Options:")
    print(f"   Enhanced Renaming: {execution.get('enhanced_renaming', True)}")
    print(
        f"   Rename Bandwidth: {execution.get('rename_bandwidth', 4)} instructions/cycle"
    )
    print(
        f"   Commit Bandwidth: {execution.get('commit_bandwidth', 4)} instructions/cycle"
    )
    print(f"   OOO Execution: {execution.get('ooo_execution', False)}")
    print(f"   OOO Window Size: {execution.get('ooo_window_size', 16)}")

    renaming = execution.get("register_renaming", {})
    print("\nRegister Renaming Parameters:")
    print(f"   Architectural Registers: {renaming.get('arch_registers', 32)}")
    print(f"   Physical Registers: {renaming.get('physical_registers', 128)}")
    print(f"   ROB Size: {renaming.get('rob_size', 64)}")
    print(f"   Issue Queue Size: {renaming.get('issue_queue_size', 32)}")


def main():
    """Main demonstration function."""
    print("Superscalar Pipeline Simulator")
    print("Configuration Management Example")
    print("=" * 50)

    try:
        demonstrate_default_configuration()
        demonstrate_custom_configuration()
        demonstrate_environment_overrides()
        demonstrate_enhanced_execution_config()
        demonstrate_configuration_profiles()
        demonstrate_configuration_validation()

        print("\nConfiguration management demonstration completed!")
        print("\nKey features:")
        print("   \u2022 Type-safe configuration with validation")
        print("   \u2022 Environment variable overrides")
        print("   \u2022 Enhanced execution options (rename/commit bandwidth, OOO)")
        print("   \u2022 Comprehensive error handling")

    except Exception as e:
        print(f"Error during demonstration: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
