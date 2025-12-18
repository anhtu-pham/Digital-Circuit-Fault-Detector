from test_generator import TestGenerator

if __name__ == "__main__":
    gen = TestGenerator()

    scenarios = ["s27", "s298f_2", "s344f_2", "s349f_2"]
    test_generation_stuck_at_faults = {
        "s27": [(16, 0), (10, 1), (12, 0), (18, 1), (17, 1), (13, 0), (6, 1), (11, 0)],
        "s298f_2": [(70, 1), (73, 0), (26, 1), (92, 0), (38, 0), (46, 1), (3, 1), (68, 0)],
        "s344f_2": [(166, 0), (71, 1), (16, 0), (91, 1), (38, 0), (5, 1), (138, 0), (91, 0)],
        "s349f_2": [(25, 1), (51, 0), (105, 1), (105, 0), (83, 1), (92, 0), (7, 0), (179, 0)]
    }
    
    for test_gen_scenario in scenarios:
        print("----------------------------------------")
        gen.build_netlist_from_file(f"../files/{test_gen_scenario}.txt")
        print("Start generating test vectors for specified stuck-at faults\n")
        for (faulty_net_name, stuck_at_value) in test_generation_stuck_at_faults[test_gen_scenario]:
            gen.generate_test_vector_by_PODEM(faulty_net_name, stuck_at_value, f"{test_gen_scenario}.txt", f"../test_files/test_gen_outputs.txt")