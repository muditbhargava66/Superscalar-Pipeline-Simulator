from pipeline import FetchStage, DecodeStage, IssueStage, ExecuteStage, MemoryAccessStage, WriteBackStage
from branch_prediction import AlwaysTakenPredictor, GsharePredictor, BimodalPredictor
from data_forwarding import DataForwardingUnit
from utils import Instruction, Scoreboard
from cache import InstructionCache, DataCache, Memory
from register_file import RegisterFile
import sys

def main():
    
    # Redirect standard output to a file
    sys.stdout = open('simulation_results.txt', 'w')
    print("Simulation Started successfully.\n")

    # Initialize instruction cache, data cache, register file, and memory
    memory = Memory(size=1024)  # Example memory size
    instruction_cache = InstructionCache(cache_size=1024, block_size=64, memory=memory, fetch_bandwidth=4)
    data_cache = DataCache(cache_size=1024, block_size=64)
    register_file = RegisterFile(num_registers=32)

    # Initialize branch predictor
    branch_predictor = BimodalPredictor(num_entries=1024)

    # Initialize pipeline stages
    fetch_stage = FetchStage(instruction_cache, branch_predictor, memory)
    decode_stage = DecodeStage(register_file)
    issue_stage = IssueStage(num_reservation_stations=4)
    execute_stage = ExecuteStage(num_functional_units=2)
    memory_access_stage = MemoryAccessStage(data_cache)
    write_back_stage = WriteBackStage(register_file)

    # Initialize data forwarding unit
    forwarding_unit = DataForwardingUnit()
    forwarding_unit.add_forwarding_path(from_stage='execute', to_stage='decode', forwarding_condition=lambda instr: True)
    forwarding_unit.add_forwarding_path(from_stage='memory', to_stage='execute', forwarding_condition=lambda instr: instr.is_memory_operation())

    # Initialize scoreboard
    scoreboard = Scoreboard(num_registers=32)

    # Pipeline loop
    while True:
        # Fetch stage
        fetched_instructions = fetch_stage.fetch()
        print(f"Fetched instructions: {fetched_instructions}")
        if not fetched_instructions:
            break

        # Decode stage
        decoded_instructions = decode_stage.decode(fetched_instructions)
        print(f"Decoded instructions: {decoded_instructions}")
        for instruction in decoded_instructions:
            forwarding_unit.forward_data(instruction, stage='decode')

        # Issue stage
        issued_instructions = issue_stage.issue(decoded_instructions)
        print(f"Issued instructions: {issued_instructions}")

        # Execute stage
        executed_instructions = []
        for instruction in issued_instructions:
            if scoreboard.is_function_unit_available(instruction.opcode):
                scoreboard.allocate_function_unit(instruction.opcode, instruction)
                result = execute_stage.execute([instruction], register_file)  # Pass register_file here
                executed_instructions.extend(result)
                forwarding_unit.forward_data(instruction, stage='execute')
        print(f"Executed instructions: {executed_instructions}")

        # Memory access stage
        memory_results = memory_access_stage.access_memory(executed_instructions)
        print(f"Memory access results: {memory_results}")
        for instruction, _ in memory_results:
            forwarding_unit.forward_data(instruction, stage='memory')

        # Write-back stage
        write_back_stage.write_back(memory_results)
        print(f"Write-back results: {memory_results}")
        for instruction, _ in memory_results:
            scoreboard.deallocate_function_unit(instruction.opcode)
            scoreboard.deallocate_register(instruction.destination)

        # Update branch predictor
        for instruction, _ in memory_results:
            if instruction.is_branch():
                actual_outcome = instruction.is_taken()
                branch_predictor.update(instruction, actual_outcome)

        # Update reservation stations and functional units
        issue_stage.update_reservation_stations(executed_instructions)
        execute_stage.update_functional_units()

    # Close the file to ensure all output is written
    print("\nSimulation completed successfully.")
    sys.stdout.close()

if __name__ == '__main__':
    main()