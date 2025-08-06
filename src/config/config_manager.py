"""
Configuration manager for loading, validating, and managing simulator configuration.

This module provides a centralized way to handle configuration from multiple sources
including files, environment variables, and command-line arguments.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Optional

from pydantic import ValidationError
import yaml

from .config_models import SimulatorConfig

# Handle imports for both package and direct execution
try:
    from ..exceptions.simulator_exceptions import ConfigurationError
except (ImportError, ValueError):
    import os
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    from exceptions.simulator_exceptions import ConfigurationError


class ConfigManager:
    """Manages simulator configuration from multiple sources."""
    
    def __init__(self):
        """Initialize the configuration manager."""
        self._config: Optional[SimulatorConfig] = None
        self._config_file: Optional[Path] = None
    
    def load_from_file(self, config_file: str | Path) -> SimulatorConfig:
        """
        Load configuration from YAML file.
        
        Args:
            config_file: Path to configuration file
            
        Returns:
            Validated configuration object
            
        Raises:
            ConfigurationError: If file cannot be loaded or is invalid
        """
        config_path = Path(config_file)
        
        if not config_path.exists():
            raise ConfigurationError(f"Configuration file not found: {config_path}")
        
        try:
            with open(config_path, encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
            
            if config_data is None:
                config_data = {}
            
            # Apply environment variable overrides
            config_data = self._apply_env_overrides(config_data)
            
            # Validate and create configuration
            self._config = SimulatorConfig(**config_data)
            self._config_file = config_path
            
            return self._config
            
        except yaml.YAMLError as e:
            raise ConfigurationError(f"Invalid YAML in {config_path}: {e}") from e
        except ValidationError as e:
            raise ConfigurationError(f"Configuration validation failed: {e}") from e
        except Exception as e:
            raise ConfigurationError(f"Failed to load configuration: {e}") from e
    
    def load_default(self) -> SimulatorConfig:
        """
        Load default configuration.
        
        Returns:
            Default configuration with environment overrides applied
        """
        config_data = self._apply_env_overrides({})
        self._config = SimulatorConfig(**config_data)
        return self._config
    
    def create_from_dict(self, config_dict: dict[str, Any]) -> SimulatorConfig:
        """
        Create configuration from dictionary.
        
        Args:
            config_dict: Configuration dictionary
            
        Returns:
            Validated configuration object
            
        Raises:
            ConfigurationError: If configuration is invalid
        """
        try:
            config_data = self._apply_env_overrides(config_dict)
            self._config = SimulatorConfig(**config_data)
            return self._config
        except ValidationError as e:
            raise ConfigurationError(f"Configuration validation failed: {e}") from e
    
    def get_config(self) -> SimulatorConfig:
        """
        Get current configuration.
        
        Returns:
            Current configuration object
            
        Raises:
            ConfigurationError: If no configuration is loaded
        """
        if self._config is None:
            raise ConfigurationError("No configuration loaded")
        return self._config
    
    def save_config(self, output_file: str | Path) -> None:
        """
        Save current configuration to file.
        
        Args:
            output_file: Output file path
            
        Raises:
            ConfigurationError: If no configuration is loaded
        """
        if self._config is None:
            raise ConfigurationError("No configuration to save")
        
        self._config.save_to_file(output_file)
    
    def update_config(self, updates: dict[str, Any]) -> SimulatorConfig:
        """
        Update current configuration with new values.
        
        Args:
            updates: Dictionary of updates to apply
            
        Returns:
            Updated configuration object
            
        Raises:
            ConfigurationError: If no configuration is loaded or update is invalid
        """
        if self._config is None:
            raise ConfigurationError("No configuration loaded")
        
        try:
            # Convert current config to dict and apply updates
            current_dict = self._config.model_dump()
            self._deep_update(current_dict, updates)
            
            # Validate updated configuration
            self._config = SimulatorConfig(**current_dict)
            return self._config
            
        except ValidationError as e:
            raise ConfigurationError(f"Configuration update validation failed: {e}") from e
    
    def _apply_env_overrides(self, config_data: dict[str, Any]) -> dict[str, Any]:
        """
        Apply environment variable overrides to configuration.
        
        Environment variables should be prefixed with SIMULATOR_ and use
        double underscores to separate nested keys.
        
        Examples:
            SIMULATOR_PIPELINE__FETCH_WIDTH=8
            SIMULATOR_DEBUG__ENABLED=true
            SIMULATOR_SIMULATION__MAX_CYCLES=50000
        """
        env_prefix = "SIMULATOR_"
        
        for key, value in os.environ.items():
            if not key.startswith(env_prefix):
                continue
            
            # Remove prefix and convert to nested dict path
            config_key = key[len(env_prefix):].lower()
            key_parts = config_key.split('__')
            
            # Convert string values to appropriate types
            converted_value = self._convert_env_value(value)
            
            # Apply to config data
            self._set_nested_value(config_data, key_parts, converted_value)
        
        return config_data
    
    def _convert_env_value(self, value: str) -> Any:
        """Convert environment variable string to appropriate type."""
        # Boolean conversion
        if value.lower() in ('true', 'yes', '1', 'on'):
            return True
        if value.lower() in ('false', 'no', '0', 'off'):
            return False
        
        # Numeric conversion
        try:
            if '.' in value:
                return float(value)
            return int(value)
        except ValueError:
            pass
        
        # Return as string
        return value
    
    def _set_nested_value(self, data: dict[str, Any], key_parts: list[str], value: Any) -> None:
        """Set a nested dictionary value using a list of keys."""
        current = data
        
        for key_part in key_parts[:-1]:
            if key_part not in current:
                current[key_part] = {}
            current = current[key_part]
        
        current[key_parts[-1]] = value
    
    def _deep_update(self, base_dict: dict[str, Any], update_dict: dict[str, Any]) -> None:
        """Recursively update a dictionary."""
        for key, value in update_dict.items():
            if key in base_dict and isinstance(base_dict[key], dict) and isinstance(value, dict):
                self._deep_update(base_dict[key], value)
            else:
                base_dict[key] = value
    
    def validate_config_file(self, config_file: str | Path) -> tuple[bool, list[str]]:
        """
        Validate a configuration file without loading it.
        
        Args:
            config_file: Path to configuration file
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        try:
            config_path = Path(config_file)
            
            if not config_path.exists():
                errors.append(f"Configuration file not found: {config_path}")
                return False, errors
            
            with open(config_path, encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
            
            if config_data is None:
                config_data = {}
            
            # Apply environment overrides
            config_data = self._apply_env_overrides(config_data)
            
            # Validate configuration
            SimulatorConfig(**config_data)
            
            return True, []
            
        except yaml.YAMLError as e:
            errors.append(f"Invalid YAML: {e}")
        except ValidationError as e:
            for error in e.errors():
                field_path = " -> ".join(str(x) for x in error['loc'])
                errors.append(f"{field_path}: {error['msg']}")
        except Exception as e:
            errors.append(f"Unexpected error: {e}")
        
        return False, errors
    
    def generate_example_config(self, output_file: str | Path) -> None:
        """
        Generate an example configuration file with all options documented.
        
        Args:
            output_file: Path for the example configuration file
        """
        example_config = SimulatorConfig()
        
        # Add comments to the YAML output
        yaml_content = example_config.model_dump_yaml()
        
        # Add header comment
        header = """# Superscalar Pipeline Simulator Configuration
# This file contains all available configuration options with their default values.
# Modify the values below to customize the simulator behavior.

"""
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(header + yaml_content)
