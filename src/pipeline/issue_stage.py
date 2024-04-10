from utils.instruction import Instruction
from utils.reservation_station import ReservationStation

class IssueStage:
    def __init__(self, num_reservation_stations):
        self.reservation_stations = [ReservationStation(i) for i in range(num_reservation_stations)]

    def issue(self, decoded_instructions):
        issued_instructions = []

        for instruction in decoded_instructions:
            # Find a free reservation station
            reservation_station = self.find_free_reservation_station()

            if reservation_station is not None:
                # Issue the instruction to the reservation station
                reservation_station.issue(instruction)
                issued_instructions.append(instruction)
            else:
                # No free reservation station available, stall the pipeline
                break

        return issued_instructions

    def find_free_reservation_station(self):
        for reservation_station in self.reservation_stations:
            if reservation_station.is_free():
                return reservation_station
        return None

    def update_reservation_stations(self, executed_instructions):
        for reservation_station in self.reservation_stations:
            reservation_station.update(executed_instructions)

    def get_ready_instructions(self):
        ready_instructions = []
        for reservation_station in self.reservation_stations:
            ready_instruction = reservation_station.get_ready_instruction()
            if ready_instruction is not None:
                ready_instructions.append(ready_instruction)
        return ready_instructions