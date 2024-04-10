# Superscalar Pipeline Simulator

## Introduction
The Superscalar Pipeline Simulator is a software tool that simulates the execution of instructions in a superscalar processor pipeline with data forwarding and branch prediction capabilities. It provides insights into the performance and behavior of the pipeline under different configurations and workloads.

## Features
- Superscalar pipeline architecture with multiple execution units
- Out-of-order execution using Tomasulo's algorithm
- Data forwarding to reduce data dependencies and improve performance
- Branch prediction using various algorithms (always taken, gshare, bimodal)
- Detailed simulation of pipeline stages: fetch, decode, issue, execute, memory access, write-back
- Configuration options for pipeline parameters and branch prediction settings
- Performance metrics and analysis, including instructions per cycle (IPC) and branch prediction accuracy
- Visualization of pipeline diagrams and simulation results
- Extensible design for adding new instructions, pipeline stages, and branch prediction algorithms

## Directory Structure
```
superscalar-pipeline-simulator/
├── src/
│   ├── __init__.py
│   ├── cache/
│   │   ├── __init__.py
│   │   └── cache.py
│   ├── register_file/
│   │   ├── __init__.py
│   │   └── register_file.py
│   ├── pipeline/
│   │   ├── __init__.py
│   │   ├── fetch_stage.py
│   │   ├── decode_stage.py
│   │   ├── issue_stage.py
│   │   ├── execute_stage.py
│   │   ├── memory_access_stage.py
│   │   └── write_back_stage.py
│   ├── branch_prediction/
│   │   ├── __init__.py
│   │   ├── always_taken_predictor.py
│   │   ├── gshare_predictor.py
│   │   └── bimodal_predictor.py
│   ├── data_forwarding/
│   │   ├── __init__.py
│   │   └── data_forwarding_unit.py
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── instruction.py
│   │   ├── scoreboard.py
│   │   ├── reservation_station.py
│   │   └── functional_unit.py
│   └── main.py
├── tests/
│   ├── __init__.py
│   ├── test_pipeline.py
│   ├── test_branch_prediction.py
│   └── test_data_forwarding.py
├── benchmarks/
│   ├── benchmark1.asm
│   └── ...
├── docs/
│   ├── design_document.md
│   └── user_guide.md
├── config.yaml
├── README.md
├── LICENSE
└── requirements.txt
```

## Getting Started

### Prerequisites
- Python 3.6 or higher
- pip package manager

### Installation
1. Clone the repository:
   ```
   git clone https://github.com/muditbhargava66/Superscalar-Pipeline-Simulator-.git
   ```

2. Navigate to the project directory:
   ```
   cd superscalar-pipeline-simulator
   ```

3. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

### Usage
1. Configure the simulator by modifying the `config.yaml` file. Specify the desired pipeline parameters, branch prediction settings, and other options.

2. Prepare the assembly code file containing the instructions to be simulated. The simulator supports a subset of the MIPS instruction set.

3. Run the simulator:
   ```
   python src/main.py --config config.yaml --code assembly_code.asm
   ```

   - `--config`: Path to the configuration file (default: `config.yaml`)
   - `--code`: Path to the assembly code file

4. The simulator will execute the instructions and provide detailed output, including pipeline stage information, data forwarding, branch predictions, and performance metrics.

5. Analyze the simulation results and visualize the pipeline diagrams and performance graphs.

## Configuration
The simulator can be configured using the `config.yaml` file. It allows you to specify various parameters such as:
- Number of pipeline stages
- Fetch and issue width
- Number of execution units
- Branch prediction algorithm and settings
- Cache configurations
- Debugging and logging options

Refer to the comments in the `config.yaml` file for detailed explanations of each configuration parameter.

## Customization and Extension
The simulator is designed to be extensible and customizable. You can add new instructions, modify pipeline stages, and implement different branch prediction algorithms. The modular structure of the code allows for easy integration of new features.

To add a new instruction:
1. Define the instruction format and encoding in the `src/utils/instruction.py` file.
2. Implement the instruction execution logic in the corresponding pipeline stage (e.g., `src/pipeline/execute_stage.py`).
3. Update the instruction decoding logic in the `src/pipeline/decode_stage.py` file.

To modify pipeline stages or add new ones:
1. Create a new file for the pipeline stage (e.g., `src/pipeline/new_stage.py`).
2. Implement the necessary logic and functionality for the stage.
3. Integrate the new stage into the pipeline flow in the `src/main.py` file.

To implement a new branch prediction algorithm:
1. Create a new file for the branch predictor (e.g., `src/branch_prediction/new_predictor.py`).
2. Implement the prediction and update logic for the branch predictor.
3. Update the branch prediction configuration in the `config.yaml` file to include the new predictor.

## Testing
The simulator includes a comprehensive test suite to ensure the correctness and reliability of the implemented features. The tests cover various aspects of the simulator, including pipeline stages, data forwarding, branch prediction, and overall functionality.

To run the tests:
```
python -m unittest discover tests
```

The test suite uses the `unittest` framework and automatically discovers and runs all the test cases in the `tests` directory.

## Documentation
The simulator provides detailed documentation to help users understand its architecture, design, and usage. The documentation includes:

- User Guide: A comprehensive guide on how to install, configure, and run the simulator. It provides step-by-step instructions and examples.

- Design Document: A technical document that describes the architecture and design of the simulator. It covers the pipeline stages, data forwarding, branch prediction, and other key components.

- API Reference: Documentation for the simulator's API, including classes, methods, and functions. It helps developers understand how to use and extend the simulator programmatically.

The documentation can be found in the `docs` directory of the project.

## Contributing
Contributions to the Superscalar Pipeline Simulator are welcome! If you find any issues or have suggestions for improvements, please open an issue on the project's GitHub repository.

To contribute code changes:
1. Fork the repository
2. Create a new branch for your feature or bug fix
3. Make the necessary code changes
4. Write tests to cover your changes
5. Ensure that all tests pass
6. Submit a pull request describing your changes

Please follow the project's coding style and guidelines when contributing.

## License
The Superscalar Pipeline Simulator is open-source software licensed under the [MIT License](LICENSE).

## Acknowledgments
The Superscalar Pipeline Simulator was inspired by the concepts and techniques presented in the following resources:
- "Computer Architecture: A Quantitative Approach" by John L. Hennessy and David A. Patterson
- "Modern Processor Design: Fundamentals of Superscalar Processors" by John P. Shen and Mikko H. Lipasti
- "Two-Level Adaptive Training Branch Prediction" by Tse-Yu Yeh and Yale N. Patt

We would like to thank the authors and researchers whose work has contributed to the development of this simulator.

## Contact
For any questions, suggestions, or feedback, please contact the project maintainer:
- Name: Mudit Bhargava
- GitHub: [muditbhargava66](https://github.com/muditbhargava66)

---