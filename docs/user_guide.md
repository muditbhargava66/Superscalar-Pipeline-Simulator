# User Guide: Superscalar Pipeline with Data Forwarding and Branch Prediction

This user guide provides instructions on how to set up, configure, and run the superscalar pipeline simulator with data forwarding and branch prediction.

## Table of Contents
1. [Introduction](#introduction)
2. [System Requirements](#system-requirements)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [Running the Simulator](#running-the-simulator)
6. [Simulator Outputs](#simulator-outputs)
7. [Customizing the Pipeline](#customizing-the-pipeline)
8. [Troubleshooting](#troubleshooting)
9. [FAQ](#faq)

## Introduction
The superscalar pipeline simulator is a software tool that simulates the execution of instructions in a superscalar processor pipeline with data forwarding and branch prediction capabilities. It allows users to analyze the performance and behavior of the pipeline under different configurations and workloads.

## System Requirements
To run the superscalar pipeline simulator, your system should meet the following requirements:
- Operating System: Windows, macOS, or Linux
- Python: Python 3.6 or higher
- Memory: At least 4 GB RAM
- Storage: At least 100 MB of free disk space

## Installation
Follow these steps to install the superscalar pipeline simulator:

1. Clone the repository from GitHub:
   ```
   git clone https://github.com/muditbhargava66/Superscalar-Pipeline-Simulator-.git
   ```

2. Navigate to the project directory:
   ```
   cd superscalar-pipeline
   ```

3. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Verify the installation by running the unit tests:
   ```
   python -m unittest discover tests
   ```

   If all the tests pass, the installation is successful.

## Configuration
The superscalar pipeline simulator can be configured using a configuration file. The default configuration file is `config.yaml` located in the project root directory.

The configuration file allows you to specify various parameters of the pipeline, such as:
- Number of pipeline stages
- Fetch width
- Issue width
- Number of functional units
- Branch predictor type and configuration
- Data forwarding paths

To modify the configuration, open the `config.yaml` file in a text editor and change the values of the desired parameters. Save the file after making the changes.

## Running the Simulator
To run the superscalar pipeline simulator, use the following command:
```
python main.py [--config CONFIG_FILE] [--benchmark BENCHMARK_FILE]
```

- `--config CONFIG_FILE`: Specifies the path to the configuration file. If not provided, the default `config.yaml` file will be used.
- `--benchmark BENCHMARK_FILE`: Specifies the path to the benchmark file containing the assembly code to be simulated. If not provided, a default benchmark will be used.

Example:
```
python main.py --config custom_config.yaml --benchmark benchmarks/benchmark1.asm
```

This command runs the simulator using the `custom_config.yaml` configuration file and the `benchmark1.asm` benchmark file.

## Simulator Outputs
During the simulation, the simulator provides real-time information about the pipeline execution, such as:
- Instruction fetch, decode, issue, execute, memory access, and write-back stages
- Branch predictions and their accuracy
- Data forwarding occurrences
- Pipeline stalls and their causes
- Execution time and instructions per cycle (IPC)

The simulation results are displayed on the console and can also be logged to a file using the logging configuration in the `config.yaml` file.

## Customizing the Pipeline
The superscalar pipeline simulator allows you to customize various aspects of the pipeline, such as adding new instructions, modifying the pipeline stages, or implementing different branch prediction algorithms.

To customize the pipeline, you can modify the relevant source code files in the `src/` directory. The key components of the pipeline are:
- `src/pipeline/`: Contains the implementation of the pipeline stages.
- `src/branch_prediction/`: Contains the implementation of branch prediction algorithms.
- `src/data_forwarding/`: Contains the implementation of the data forwarding unit.
- `src/utils/`: Contains utility classes and functions used throughout the project.

After making the desired modifications, rebuild the project and run the simulator with the updated code.

## Troubleshooting
If you encounter any issues while running the superscalar pipeline simulator, consider the following troubleshooting steps:

1. Verify that your system meets the requirements specified in the [System Requirements](#system-requirements) section.

2. Ensure that you have followed the installation instructions correctly and have installed all the required dependencies.

3. Check the configuration file (`config.yaml`) for any incorrect or missing parameters.

4. Verify that the benchmark file is in the correct format and contains valid assembly code.

5. If you encounter errors or exceptions during the simulation, refer to the error messages and traceback for clues on the cause of the issue.

6. Consult the [FAQ](#faq) section for common questions and solutions.

If the issue persists, please open an issue on the project's GitHub repository, providing detailed information about the problem and the steps to reproduce it.

## FAQ

**Q: Can I use a different assembly language other than MIPS for the benchmarks?**

A: The current version of the superscalar pipeline simulator is designed to work with MIPS assembly language. If you want to use a different assembly language, you would need to modify the simulator to support the syntax and semantics of that language.

**Q: How can I analyze the performance of the pipeline in more detail?**

A: The simulator provides basic performance metrics such as execution time and instructions per cycle (IPC). For more detailed analysis, you can modify the code to collect additional statistics or use external performance analysis tools that are compatible with the simulator's output.

**Q: Can I contribute to the development of the superscalar pipeline simulator?**

A: Yes, contributions to the project are welcome! If you have any improvements, bug fixes, or new features to propose, please submit a pull request on the project's GitHub repository. Make sure to follow the contribution guidelines outlined in the repository.

**Q: How can I report a bug or issue with the simulator?**

A: If you encounter any bugs or issues with the superscalar pipeline simulator, please open an issue on the project's GitHub repository. Provide a clear description of the problem, steps to reproduce it, and any relevant error messages or logs.

**Q: Is there a graphical user interface (GUI) for the simulator?**

A: The current version of the simulator does not include a GUI. It is primarily designed to be used through the command line interface (CLI). However, you can explore the possibility of integrating a GUI as a future enhancement to the project.

---