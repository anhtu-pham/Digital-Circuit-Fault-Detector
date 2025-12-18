from simulation import Simulation
import random
import matplotlib.pyplot as plt

if __name__ == "__main__":
    sim = Simulation()
    random_gen = random.Random(5)

    scenarios = ["s27", "s298f_2", "s344f_2", "s349f_2"]
    fault_simulation_input_vectors = {
        "s27": ["1101101", "0101001"],
        "s298f_2": ["10101011110010101", "11101110101110111"],
        "s344f_2": ["101010101010111101111111", "111010111010101010001100"],
        "s349f_2": ["101000000010101011111111", "111111101010101010001111"]
    }
    max_num_tests = {
        "s27": 20,
        "s298f_2": 40,
        "s344f_2": 50,
        "s349f_2": 50
    }

    for sim_scenario in scenarios:
        print("----------------------------------------")
        sim.build_netlist_from_file(f"../files/{sim_scenario}.txt")
        input_vector_size = len(sim.netlist.input_nets)


        sim.run_simulations_with_file(f"../test_files/{sim_scenario}.chat")


        print("Start running fault simulations\n")
        sim.place_stuck_at_faults()
        for input_vector in fault_simulation_input_vectors[sim_scenario]:
            sim.run_fault_simulation_with_input(input_vector, True, f"{sim_scenario}.txt", f"../test_files/fault_sim_outputs.txt")
        print("Completed fault simulations\n\n")


        print("Start running fault simulations with random test vectors")
        sim.place_stuck_at_faults()
        num_faults = sim.count_stuck_at_faults()
        sim.reset_detected_faults()
        num_tests_range = range(1, max_num_tests[sim_scenario] + 1)
        fault_coverages = []
        for i in num_tests_range:
            random_test_vector = ''.join(random_gen.choice("01") for _ in range(input_vector_size))
            detected_faults = sim.run_fault_simulation_with_input(random_test_vector, False, f"{sim_scenario}.txt")
            fault_coverages.append(len(detected_faults) / num_faults * 100)
        
        print("Completed running fault simlations with random test vectors")
        print("Generate plot for fault coverage vs. number of random test vectors\n")
        plt.figure()
        plt.plot(num_tests_range, fault_coverages, marker='o')
        plt.xticks(range(0, max_num_tests[sim_scenario] + 1, 2))
        plt.yticks(range(0, 101, 5))
        plt.xlabel("Number of random test vectors")
        plt.ylabel("Fault coverage (%)")
        plt.title(f"Fault coverage vs. Number of random test vectors for circuit {sim_scenario}.txt")
        plt.grid(True)
    plt.show()