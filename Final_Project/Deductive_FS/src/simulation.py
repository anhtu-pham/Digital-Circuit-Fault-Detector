from netlist import Netlist

class Simulation:
    def __init__(self):
        self.netlist = None

    def build_netlist_from_file(self, netlist_filepath: str):
        self.netlist = Netlist()
        self.netlist.build_from_file(netlist_filepath)
        return self.netlist

    def run_simulation_with_input(self, input_line: str):
        assert self.netlist != None
        print(f"Simulation with input {input_line}")

        # Reset every net as unassigned
        for net in self.netlist.nets_by_name.values():
            net.assigned = False

        # Reset every gate as unvisited
        for gate in self.netlist.gates:
            gate.visited = False

        # Create stack of gates for evaluation
        gates_stack = []

        # For each input bit in test
        for i, value in enumerate(input_line):
            # Check if user-defined logic value is valid, assign logical value to each input net, set input net as assigned
            value = int(value)
            if value not in [0, 1]:
                print(f"Invalid input with value {value}")
                return
            input_net = self.netlist.input_nets[i]
            input_net.logic_value = value
            input_net.assigned = True
            # Push unvisited gates that have all inputs assigned onto stack, set these gates as visited
            for des_gate in input_net.des_gates:
                if (not des_gate.visited) and des_gate.all_inputs_assigned():
                    des_gate.visited = True
                    gates_stack.append(des_gate)

        # While stack still has gate(s) remaining
        while len(gates_stack) > 0:
            # Pop gate from stack
            gate = gates_stack.pop()
            # Evaluate gate to assign corresponding logical value to output net, set output net as assigned
            gate.evaluate()
            gate.out_net.assigned = True
            # Push unevaluated gates that have all inputs assigned onto stack, set these gates as visited
            for des_gate in gate.out_net.des_gates:
                if (not des_gate.visited) and des_gate.all_inputs_assigned():
                    des_gate.visited = True
                    gates_stack.append(des_gate)

        # Print output
        print("Output: ", end='')
        for output_net in self.netlist.output_nets:
            print(f"{output_net.logic_value}", end='')
        print("\n")

    def run_simulations_with_file(self, test_filepath: str):
        assert self.netlist != None
        try:
            with open(test_filepath, 'r') as file:
                print(f"Start running circuit simulations with file {test_filepath}\n")
                for file_line in file:
                    self.run_simulation_with_input(file_line.strip())
                print("Completed circuit simulations\n\n")
        except FileNotFoundError:
            print(f"File {test_filepath} was not found!")
        except Exception as exception:
            print(f"Exception occurred: {exception}")

    
    # If faults_filepath is not specified, simulate all faults in the net
    # If faults_filepath is specified, take faults from file for simulation
    def place_stuck_at_faults(self, faults_filepath: str = None):
        assert self.netlist != None

        if faults_filepath == None:
            for net in self.netlist.nets_by_name.values():
                net.stuck_at_values = {0, 1}
        else:
            # Reset all nets' stuck-at values
            for net in self.netlist.nets_by_name.values():
                net.stuck_at_values = set()

            try:
                with open(faults_filepath, "r") as file:
                    for line in file:
                        line_info = line.strip().split()
                        if (len(line_info) == 2):
                            net_name = int(line_info[0])
                            stuck_at_value = int(line_info[1])
                            self.netlist.nets_by_name.get(net_name).stuck_at_values.add(stuck_at_value)
            
            except FileNotFoundError:
                print(f"File {faults_filepath} was not found!")
            except Exception as exception:
                print(f"Exception occurred: {exception}")

    # Reset all nets' fault lists
    def reset_detected_faults(self):
        assert self.netlist != None
        for net in self.netlist.nets_by_name.values():
            net.faults = set()

    # If output_filepath is specified, print results and write results into file specified
    def run_fault_simulation_with_input(self, input_line: str, reset_detection: bool, circuit_name: str, output_filepath: str = None):
        assert self.netlist != None
        
        if (reset_detection):
            self.reset_detected_faults()

        # Reset every net as unassigned
        for net in self.netlist.nets_by_name.values():
            net.assigned = False

        # Reset every gate as unvisited
        for gate in self.netlist.gates:
            gate.visited = False

        # Create stack of gates for fault propagation
        gates_stack = []

        # For each input bit in test
        for i, value in enumerate(input_line):
            # Check if user-defined logical value is valid, find fault of each input net, set input net as assigned
            value = int(value)
            if value not in [0, 1]:
                print(f"Invalid input with value {value}")
                return
            input_net = self.netlist.input_nets[i]
            input_net.logic_value = value
            matching_stuck_at_value = int(not value)
            if matching_stuck_at_value in input_net.stuck_at_values:
                input_net.faults.add((input_net.name, matching_stuck_at_value))
            input_net.assigned = True
            # Push unvisited gates that have all inputs assigned onto stack, set these gates as visited
            for des_gate in input_net.des_gates:
                if (not des_gate.visited) and des_gate.all_inputs_assigned():
                    des_gate.visited = True
                    gates_stack.append(des_gate)

        # While stack still has gate(s) remaining
        while len(gates_stack) > 0:
            # Pop gate from stack
            gate = gates_stack.pop()
            # Propagate faults to output net, set output net as assigned
            valid = gate.perform_fault_list_propagation()
            if not valid:
                return
            gate.out_net.assigned = True
            # Push unevaluated gates that have all inputs assigned onto stack, set these gates as visited
            for des_gate in gate.out_net.des_gates:
                if (not des_gate.visited) and des_gate.all_inputs_assigned():
                    des_gate.visited = True
                    gates_stack.append(des_gate)

        detected_faults = set()
        for output_net in self.netlist.output_nets:
            detected_faults = detected_faults.union(output_net.faults)

        if output_filepath != None:
            sorted_detected_faults = sorted(detected_faults, key = lambda fault: fault[0])
            # Print and write output
            try:
                with open(output_filepath, "a") as output_file:
                    if reset_detection:
                        print(f"Circuit: {circuit_name}   Input Vector: {" ".join(input_line)}\n\n------FAULTS DETECTED -----------")
                        output_file.write(f"Circuit: {circuit_name}   Input Vector: {" ".join(input_line)}\n\n------FAULTS DETECTED -----------\n")
                        for detected_fault in sorted_detected_faults:
                            print(f"{detected_fault[0]:>5} stuck at  {detected_fault[1]}")
                            output_file.write(f"{detected_fault[0]:>5} stuck at  {detected_fault[1]}\n")
                        print(f"Number of faults detected: {len(sorted_detected_faults)}\n")
                        output_file.write(f"Number of faults detected: {len(sorted_detected_faults)}\n\n")
                    else:
                        print(f"Circuit: {circuit_name}   Input Vector: {" ".join(input_line)}\n\n------ALL FAULTS DETECTED SO FAR -----------")
                        output_file.write(f"Circuit: {circuit_name}   Input Vector: {" ".join(input_line)}\n\n------ALL FAULTS DETECTED SO FAR -----------\n")
                        for detected_fault in sorted_detected_faults:
                            print(f"{detected_fault[0]:>5} stuck at  {detected_fault[1]}")
                            output_file.write(f"{detected_fault[0]:>5} stuck at  {detected_fault[1]}\n")
                        print(f"Total number of faults detected so far: {len(sorted_detected_faults)}\n")
                        output_file.write(f"Total number of faults detected so far: {len(sorted_detected_faults)}\n\n")
            except FileNotFoundError:
                print(f"File {output_filepath} was not found!")
            except Exception as exception:
                print(f"Exception occurred: {exception}")
        
        return detected_faults

    def count_stuck_at_faults(self):
        assert self.netlist != None
        count = 0
        for net in self.netlist.nets_by_name.values():
            count += len(net.stuck_at_values)
        return count