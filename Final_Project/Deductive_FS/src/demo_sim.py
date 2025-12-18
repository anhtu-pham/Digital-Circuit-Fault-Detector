from simulation import Simulation
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--circuit", type=str, required=True, help="Circuit in Deductive_FS/files/ directory")
    parser.add_argument("--inputs", type=lambda input_vectors: input_vectors.split(","), required=True, help="Comma-separated list of input vectors")
    parser.add_argument("--output", type=str, required=True, help="Output filepath")
    parser.add_argument("--faults", type=str, required=False, default=None, help="Faults filepath")
    parser.add_argument("--cumulative", action="store_true", help="Whether to do cumulative fault simulations")

    arguments = parser.parse_args()

    circuit_name = arguments.circuit
    netlist_filepath = f"../files/{circuit_name}"

    fault_sim_faults_filepath = arguments.faults
    fault_sim_inputs = arguments.inputs
    fault_sim_output_filepath = arguments.output
    is_cumulative = arguments.cumulative

    sim = Simulation()

    sim.build_netlist_from_file(netlist_filepath)
    sim.place_stuck_at_faults(fault_sim_faults_filepath)
    for fault_sim_input in fault_sim_inputs:
        sim.run_fault_simulation_with_input(fault_sim_input, not is_cumulative, circuit_name, fault_sim_output_filepath)