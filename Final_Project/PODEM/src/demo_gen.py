from simulation import Simulation
from test_generator import TestGenerator
import argparse

def fault_info(fault_str):
    (faulty_net_info, stuck_at_info) = fault_str.split(",")
    return (int(faulty_net_info), int(stuck_at_info))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--circuit", type=str, required=True, help="Circuit in PODEM/files/ directory")
    parser.add_argument("--faults", type=fault_info, required=True, nargs="+", help="Space-separated list of stuck-at faults, each in the form of <faulty net>,<stuck-at value>")
    parser.add_argument("--output", type=str, required=True, help="Output filepath")
    parser.add_argument("--enable_sim", action="store_true", help="Whether to do fault simulation with test vector generated")

    arguments = parser.parse_args()

    circuit_name = arguments.circuit
    netlist_filepath = f"../files/{circuit_name}"

    test_gen_faults = arguments.faults
    output_filepath = arguments.output
    is_sim_enabled = arguments.enable_sim

    sim = None
    gen = TestGenerator()

    gen.build_netlist_from_file(netlist_filepath)
    if is_sim_enabled:
        sim = Simulation()
        sim.build_netlist_from_file(netlist_filepath)
        sim.place_stuck_at_faults()

    for (faulty_net_name, stuck_at_value) in test_gen_faults:
        test_vector = gen.generate_test_vector_by_PODEM(faulty_net_name, stuck_at_value, circuit_name, output_filepath)

        if is_sim_enabled and (test_vector != None):
            sim.run_fault_simulation_with_input(test_vector, True, circuit_name, output_filepath)