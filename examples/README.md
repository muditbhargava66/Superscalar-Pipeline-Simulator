# Examples

This directory contains comprehensive examples demonstrating the capabilities of the Superscalar Pipeline Simulator. Each example focuses on specific aspects of the simulator and provides practical usage patterns.

## Available Examples

### 1. Basic Simulation (`basic_simulation.py`)
**Purpose**: Introduction to the simulator with simple assembly code execution.

**Features Demonstrated**:
- Basic configuration setup
- Assembly code parsing
- Simple instruction execution
- Performance metrics calculation

**Usage**:
```bash
python examples/basic_simulation.py
```

**Best For**: New users getting started with the simulator.

### 2. Advanced Pipeline Features (`advanced_pipeline_features.py`)
**Purpose**: Showcase advanced processor features and research capabilities.

**Features Demonstrated**:
- Tournament and Perceptron branch predictors
- Non-blocking cache with MSHR support
- Enhanced register renaming with ROB
- Processor power and energy modeling

**Usage**:
```bash
python examples/advanced_pipeline_features.py
```

**Best For**: Researchers and advanced users exploring cutting-edge processor features.

### 3. Configuration Management (`configuration_management.py`)
**Purpose**: Comprehensive guide to simulator configuration and customization.

**Features Demonstrated**:
- Default configuration exploration
- Custom configuration creation and validation
- Environment variable overrides
- Configuration profiles for different use cases
- Error handling and validation

**Usage**:
```bash
python examples/configuration_management.py
```

**Best For**: Users who need to customize simulator behavior for specific research or educational needs.

### 4. Performance Analysis (`performance_analysis.py`)
**Purpose**: Performance profiling, bottleneck identification, and optimization guidance.

**Features Demonstrated**:
- Real-time performance monitoring
- Pipeline bottleneck analysis
- Memory usage profiling and leak detection
- Benchmark comparison and evaluation
- Power consumption analysis

**Usage**:
```bash
python examples/performance_analysis.py
```

**Best For**: Performance engineers and researchers analyzing processor efficiency.

### 5. Error Handling Showcase (`error_handling_showcase.py`)
**Purpose**: Comprehensive demonstration of error handling and debugging capabilities.

**Features Demonstrated**:
- Exception hierarchy and error types
- Configuration validation errors
- Instruction parsing error handling
- Pipeline and memory exceptions
- Error recovery mechanisms
- Debugging and diagnostic features

**Usage**:
```bash
python examples/error_handling_showcase.py
```

**Best For**: Developers and researchers who need robust error handling and debugging capabilities.

## Status: All Examples Working ✅

All example files have been tested and are working correctly with the current simulator API. Each example demonstrates different aspects of the simulator and provides practical usage patterns for various use cases.

## Running Examples

### Prerequisites
- Python 3.10 or higher
- All simulator dependencies installed
- Simulator source code in the `src/` directory

### Basic Execution
```bash
# Run from the project root directory
python examples/<example_name>.py
```

### With Custom Configuration
```bash
# Set environment variables for configuration
export SIMULATOR_PIPELINE_WIDTH=8
export SIMULATOR_CACHE_L1D_SIZE=64
python examples/advanced_pipeline_features.py
```

## Example Output

Each example provides detailed output showing:
- Configuration parameters
- Execution progress
- Performance metrics
- Analysis results
- Recommendations and insights

## Educational Use

These examples are designed for:

### Computer Architecture Courses
- **Basic Simulation**: Introduction to pipeline concepts
- **Advanced Features**: Modern processor techniques
- **Performance Analysis**: Optimization methodologies

### Research Applications
- **Configuration Management**: Experimental setup
- **Advanced Features**: Algorithm evaluation
- **Error Handling**: Robust simulation development

### Industry Training
- **Performance Analysis**: Processor optimization
- **Configuration Management**: Product customization
- **Error Handling**: Production-quality development

## Customization

Each example can be modified to:
- Test different configurations
- Analyze specific workloads
- Evaluate new algorithms
- Generate custom reports

## Integration

Examples can be integrated into:
- Automated testing frameworks
- Continuous integration pipelines
- Educational assessment tools
- Research experiment workflows

## Support

For questions about examples:
1. Check the inline documentation in each file
2. Review the main project documentation
3. Examine the source code in `src/`
4. Open an issue on the project repository

## Contributing

To contribute new examples:
1. Follow the existing code structure and style
2. Include comprehensive documentation
3. Add error handling and validation
4. Provide clear usage instructions
5. Test with different configurations