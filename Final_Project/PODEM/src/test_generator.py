import random
from gate import GateType
from netlist import Netlist

class TestGenerator:
    def __init__(self):
        self.netlist = None
        self.D_frontier = None

    def build_netlist_from_file(self, netlist_filepath: str):
        self.netlist = Netlist()
        self.netlist.build_from_file(netlist_filepath)
        return self.netlist


    def generate_random_test_vector(self, random_gen: random.Random, size: int):
        return ''.join(random_gen.choice("01") for _ in range(size))
    

    def objective_PODEM(self, faulty_net, stuck_at_value):
        if (faulty_net.is_fault_activated == None):
            return (faulty_net, int(not stuck_at_value))
        
        D_gate = list(self.D_frontier)[0]
        for in_net in D_gate.in_nets:
            if (in_net.logic_value == None and in_net.faulty_value == None):
                match D_gate.gate_type:
                    case GateType.XOR | GateType.XNOR:
                        return (in_net, D_gate.has_inversion)
                    case _:
                        return (in_net, int(not D_gate.controlling_values[0]))
        return None

    def backtrace_PODEM(self, objective):
        (current_net, current_value) = objective
        while (current_net.src_gate != None):
            current_gate = current_net.src_gate
            (current_net, current_value) = current_gate.backtrace(current_value)
        return (current_net, current_value)

    def imply_PODEM(self, input_net, assigned_value, faulty_net, stuck_at_value):
        # Just activate (already assign) if input net is faulty net
        if (input_net.name == faulty_net.name):
            faulty_net.is_fault_activated = True
        else:
            input_net.logic_value = assigned_value
            input_net.faulty_value = assigned_value

        # Create stack of gates for evaluation
        gates_stack = []

        for des_gate in input_net.des_gates:
            gates_stack.append(des_gate)

        # While stack still has gate(s) remaining
        while len(gates_stack) > 0:
            # Pop gate from stack
            gate = gates_stack.pop()

            # Evaluate gate to find corresponding values for output net
            (logic_value, faulty_value) = gate.evaluate_verbose_with_possible_fault()
            is_output_changed = (logic_value != gate.out_net.logic_value or faulty_value != gate.out_net.faulty_value)

            # Handle if gate's output net is faulty net
            if (gate.out_net.name == faulty_net.name):
                if (logic_value == None):
                    is_output_changed = False
                    faulty_net.is_fault_activated = None
                elif (logic_value == stuck_at_value):
                    faulty_net.is_fault_activated = False
                    return
                else:
                    faulty_net.is_fault_activated = True
            
            if is_output_changed:
                # Faulty net should keep D / Db instead of taking in 0 or 1
                if (gate.out_net.name != faulty_net.name):
                    gate.out_net.logic_value = logic_value
                    gate.out_net.faulty_value = faulty_value

                is_D_or_Db_created = False
                if (gate.out_net.logic_value != None and gate.out_net.faulty_value != None):
                    self.D_frontier.discard(gate)
                    is_D_or_Db_created = (gate.out_net.logic_value == int(not gate.out_net.faulty_value))

                for des_gate in gate.out_net.des_gates:
                    # If gate has output x and an input D/Db, add gate to D-frontier
                    if (is_D_or_Db_created and des_gate.out_net.logic_value == None and des_gate.out_net.faulty_value == None):
                        self.D_frontier.add(des_gate)
                    # Push gate onto stack
                    gates_stack.append(des_gate)

    def has_no_x_path_PODEM(self):
        gates_set = set()
        
        for output_net in self.netlist.output_nets:
            if (output_net.src_gate != None and output_net.logic_value == None and output_net.faulty_value == None):
                gates_set.add(output_net.src_gate)

        while (len(gates_set) > 0):
            gate = gates_set.pop()
            for in_net in gate.in_nets:
                if (in_net.logic_value == None and in_net.faulty_value == None):
                    if (in_net.src_gate != None):
                        gates_set.add(in_net.src_gate)
                elif (in_net.logic_value == int(not in_net.faulty_value)):
                    return False
        return True

    def run_PODEM(self, faulty_net, stuck_at_value):
        # If faulty net is activated and fault's effect is propagated to netlist's output net, PODEM succeeds
        if (faulty_net.is_fault_activated == True):
            for net in self.netlist.output_nets:
                if (net.logic_value != None and net.faulty_value != None and net.logic_value == int(not net.faulty_value)):
                    return True
            
        # If fault can't be activated (even if fault is at output), PODEM fails
        if (faulty_net.is_fault_activated == False):
            return False
        
        # If fault is not at output net, then if D-frontier is empty or there is no x-path to output, PODEM fails
        if (len(faulty_net.des_gates) > 0):
            if (len(self.D_frontier) == 0 or self.has_no_x_path_PODEM()):
                return False

        objective = self.objective_PODEM(faulty_net, stuck_at_value)
        if objective != None:
            (input_net, assigned_value) = self.backtrace_PODEM(objective)

            self.imply_PODEM(input_net, assigned_value, faulty_net, stuck_at_value)
            if (self.run_PODEM(faulty_net, stuck_at_value)):
                return True
            
            self.imply_PODEM(input_net, int(not assigned_value), faulty_net, stuck_at_value)
            if (self.run_PODEM(faulty_net, stuck_at_value)):
                return True
            
            self.imply_PODEM(input_net, None, faulty_net, stuck_at_value)
        return False
    
    def generate_test_vector_by_PODEM(self, faulty_net_name: int, stuck_at_value: int, circuit_name: str, output_filepath: str):
        assert self.netlist != None

        if stuck_at_value not in [0, 1]:
            print(f"Invalid stuck-at value {stuck_at_value}")
            return

        faulty_net = self.netlist.nets_by_name.get(faulty_net_name)
        if (faulty_net == None):
            print(f"Invalid net {faulty_net_name}")
            return

        self.D_frontier = set()
        faulty_net.is_fault_activated = None
        for net in self.netlist.nets_by_name.values():
            net.logic_value = None
            net.faulty_value = None

        faulty_net.logic_value = int(not stuck_at_value)
        faulty_net.faulty_value = stuck_at_value
        self.D_frontier.update(faulty_net.des_gates)

        with open(output_filepath, "a") as output_file:
            print(f"Circuit: {circuit_name}   Input fault: Net {faulty_net_name} s-a-{stuck_at_value}\n")
            output_file.write(f"Circuit: {circuit_name}   Input fault: Net {faulty_net_name} s-a-{stuck_at_value}\n\n")
            if (self.run_PODEM(faulty_net, stuck_at_value)):
                print("Test vector generated: ", end='')
                output_file.write("Test vector generated: ")
                test_vector = ""
                
                for input_net in self.netlist.input_nets:
                    input_net_value = input_net.logic_value if input_net.logic_value != None else 0
                    print(f"{input_net_value}", end='')
                    output_file.write(f"{input_net_value}")
                    test_vector = test_vector + str(input_net_value)
                print("\n")
                output_file.write("\n\n")
                return test_vector
            else:
                print("The fault is undetectable\n")
                output_file.write("The fault is undetectable\n\n")
                return None