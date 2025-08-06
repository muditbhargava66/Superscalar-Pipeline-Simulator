#!/usr/bin/env python3
"""
Example demonstrating the enhanced configuration management system.

This example shows how to use the new Pydantic-based configuration
system with validation, environment variable overrides, and error handling.
"""

import os
from pathlib import Path
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from config import ConfigManager, PipelineConfig, SimulatorConfig
from config.config_manager import ConfigurationError


def main():
    """Demonstrate enhanced configuration features."""
    print("Enhanced Configuration Management Example")
    print("=" * 50)
    
    # 1. Create configuration manager
    config_manager = ConfigManager()
    
    # 2. Load default configuration
    print("\n1. Loading default configuration...")
    try:
        default_config = config_manager.load_default()
        print("✅ Default config loaded successfully")
        print(f"   Pipeline stages: {default_config.pipeline.num_stages}")
        print(f"   Fetch width: {default_config.pipeline.fetch_width}")
        print(f"   Branch predictor: {default_config.branch_predictor.type}")
    except ConfigurationError as e:
        print(f"❌ Failed to load default config: {e}")
        return
    
    # 3. Demonstrate validation
    print("\n2. Testing configuration validation...")
    try:
        # This should fail validation
        invalid_config = {
            'pipeline': {
                'num_stages': 15,  # Too many stages (max is 10)
                'fetch_width': 0,  # Too small (min is 1)
            }
        }
        config_manager.create_from_dict(invalid_config)
        print("❌ Validation should have failed!")
    except ConfigurationError as e:
        print(f"✅ Validation correctly caught error: {e}")
    
    # 4. Demonstrate environment variable overrides
    print("\n3. Testing environment variable overrides...")
    
    # Set some environment variables
    os.environ['SIMULATOR_PIPELINE__FETCH_WIDTH'] = '8'
    os.environ['SIMULATOR_DEBUG__ENABLED'] = 'true'
    os.environ['SIMULATOR_SIMULATION__MAX_CYCLES'] = '50000'
    
    try:
        env_config = config_manager.load_default()
        print("✅ Environment overrides applied:")
        print(f"   Fetch width: {env_config.pipeline.fetch_width} (was 4)")
        print(f"   Debug enabled: {env_config.debug.enabled} (was False)")
        print(f"   Max cycles: {env_config.simulation.max_cycles} (was 10000)")
    except ConfigurationError as e:
        print(f"❌ Failed to apply environment overrides: {e}")
    
    # Clean up environment variables
    for key in ['SIMULATOR_PIPELINE__FETCH_WIDTH', 'SIMULATOR_DEBUG__ENABLED',
                'SIMULATOR_SIMULATION__MAX_CYCLES']:
        os.environ.pop(key, None)
    
    # 5. Demonstrate configuration updates
    print("\n4. Testing configuration updates...")
    try:
        config_manager.get_config()
        updates = {
            'pipeline': {
                'issue_width': 6,
            },
            'branch_predictor': {
                'num_entries': 2048,
            }
        }
        
        updated_config = config_manager.update_config(updates)
        print("✅ Configuration updated successfully:")
        print(f"   Issue width: {updated_config.pipeline.issue_width}")
        print(f"   Predictor entries: {updated_config.branch_predictor.num_entries}")
    except ConfigurationError as e:
        print(f"❌ Failed to update configuration: {e}")
    
    # 6. Generate example configuration file
    print("\n5. Generating example configuration file...")
    try:
        example_file = Path("example_config.yaml")
        config_manager.generate_example_config(example_file)
        print(f"✅ Example configuration saved to: {example_file}")
        
        # Show first few lines
        with open(example_file) as f:
            lines = f.readlines()[:10]
            print("   First few lines:")
            for line in lines:
                print(f"   {line.rstrip()}")
        
        # Clean up
        example_file.unlink()
        
    except Exception as e:
        print(f"❌ Failed to generate example config: {e}")
    
    # 7. Demonstrate configuration validation
    print("\n6. Testing configuration file validation...")
    
    # Create a test config file
    test_config_file = Path("test_config.yaml")
    try:
        # Create valid config
        valid_config = config_manager.get_config()
        valid_config.save_to_file(test_config_file)
        
        # Validate it
        is_valid, errors = config_manager.validate_config_file(test_config_file)
        if is_valid:
            print("✅ Configuration file validation passed")
        else:
            print(f"❌ Configuration file validation failed: {errors}")
        
        # Clean up
        test_config_file.unlink()
        
    except Exception as e:
        print(f"❌ Failed to test config validation: {e}")
    
    print("\n" + "=" * 50)
    print("Enhanced configuration management example completed!")


if __name__ == '__main__':
    main()
