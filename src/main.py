from src.pipeline import FetchStage, DecodeStage, IssueStage, ExecuteStage, MemoryAccessStage, WriteBackStage
from src.branch_prediction import AlwaysTakenPredictor, GsharePredictor, BimodalPredictor
from src.data_forwarding import DataForwardingUnit
from src.utils import Instruction, Scoreboard

def main():
    # Initialize pipeline stages
    fetch_stage = FetchStage(instruction_cache, branch_predictor)
    decode_stage = DecodeStage(register_file)
    issue_stage = IssueStage(num_reservation_stations)
    execute_stage = ExecuteStage(num_functional_units)
    memory_access_stage = MemoryAccessStage(data_cache)
    write_back_stage = WriteBackStage(register_file)

    # Initialize branch predictor
    branch_predictor = BimodalPredictor(num_entries=1024)

    # Initialize data forwarding unit
    forwarding_unit = DataForwardingUnit()
    forwarding_unit.add_forwarding_path(from_stage='execute', to_stage='decode', forwarding_condition=lambda instr: True)
    forwarding_unit.add_forwarding_path(from_stage='memory', to_stage='execute', forwarding_condition=lambda instr: instr.is_load())

    # Initialize scoreboard
    scoreboard = Scoreboard(num_registers=32)

    # Pipeline loop
    while True:
        # Fetch stage
        fetched_instructions = fetch_stage.fetch()
        if not fetched_instructions:
            break

        # Decode stage
        decoded_instructions = decode_stage.decode(fetched_instructions)
        for instruction in decoded_instructions:
            forwarding_unit.forward_data(instruction, stage='decode')

        # Issue stage
        issued_instructions = issue_stage.issue(decoded_instructions)

        # Execute stage
        executed_instructions = []
        for instruction in issued_instructions:
            if scoreboard.is_function_unit_available(instruction.opcode):
                scoreboard.allocate_function_unit(instruction.opcode, instruction)
                result = execute_stage.execute(instruction)
                executed_instructions.append((instruction, result))
                forwarding_unit.forward_data(instruction, stage='execute')

        # Memory access stage
        memory_results = memory_access_stage.access_memory(executed_instructions)
        for instruction, _ in memory_results:
            forwarding_unit.forward_data(instruction, stage='memory')

        # Write-back stage
        write_back_stage.write_back(memory_results)
        for instruction, _ in memory_results:
            scoreboard.deallocate_function_unit(instruction.opcode)
            scoreboard.deallocate_register(instruction.destination)

        # Update branch predictor
        for instruction, _ in memory_results:
            if isinstance(instruction, BranchInstruction):
                actual_outcome = instruction.is_taken()
                branch_predictor.update(instruction, actual_outcome)

        # Update reservation stations and functional units
        issue_stage.update_reservation_stations(executed_instructions)
        execute_stage.update_functional_units()

if __name__ == '__main__':
    main()