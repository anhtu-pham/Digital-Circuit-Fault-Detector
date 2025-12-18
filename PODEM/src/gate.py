from net import Net
from enum import Enum

class GateType(Enum):
    BUF = "BUF"
    AND = "AND"
    OR = "OR"
    XOR = "XOR"
    INV = "INV"
    NAND = "NAND"
    NOR = "NOR"
    XNOR = "XNOR"

controlling_values_dict = {
    GateType.BUF: [0, 1],
    GateType.AND: [0],
    GateType.OR: [1],
    GateType.XOR: [],
    GateType.INV: [0, 1],
    GateType.NAND: [0],
    GateType.NOR: [1],
    GateType.XNOR: []
}

gates_with_inversion = {GateType.INV, GateType.NAND, GateType.NOR, GateType.XNOR}

class Gate:
    def __init__(self, gate_type: GateType):
        if gate_type == None:
            raise ValueError("Missing gate type")
        self.gate_type = gate_type
        self.in_nets = []
        self.out_net = None
        self.visited = False

        self.controlling_values = controlling_values_dict[gate_type]
        self.has_inversion = self.gate_type in gates_with_inversion

    def __repr__(self):
        return f"{self.gate_type} gate -> output net {self.out_net.name}"

    def set_connecting_nets(self, in_nets: list[Net], out_net: Net):
        self.in_nets = in_nets
        self.out_net = out_net
    

    def evaluate(self):
        result = self.in_nets[0].logic_value

        for i in range(1, len(self.in_nets)):
            in_net_value = self.in_nets[i].logic_value
            match self.gate_type:
                case GateType.AND | GateType.NAND: result = result & in_net_value
                case GateType.OR | GateType.NOR: result = result | in_net_value
                case GateType.XOR | GateType.XNOR: result = result ^ in_net_value
        
        if (self.has_inversion):
            result = int(not result)
        self.out_net.logic_value = result
    

    def evaluate_verbose(self, in_nets_values):
        result = in_nets_values[0]
        
        for i in range(1, len(in_nets_values)):
            in_net_value = in_nets_values[i]
            match self.gate_type:
                case GateType.AND | GateType.NAND:
                    if (result == 0 or in_net_value == 0):
                        return 0 ^ self.has_inversion
                    else:
                        result = 1 if (result == 1 and in_net_value == 1) else None
                case GateType.OR | GateType.NOR:
                    if (result == 1 or in_net_value == 1):
                        return 1 ^ self.has_inversion
                    else:
                        result = 0 if (result == 0 and in_net_value == 0) else None
                case GateType.XOR | GateType.XNOR:
                    if (result == None or in_net_value == None):
                        return None
                    else:
                        result = result ^ in_net_value
        
        if (self.has_inversion and result != None):
            result = int(not result)
        return result
    
    def evaluate_verbose_with_possible_fault(self):
        faulty_in_nets_values = list()
        in_nets_values = list()
        for in_net in self.in_nets:
            faulty_in_nets_values.append(in_net.faulty_value)
            in_nets_values.append(in_net.logic_value)
        
        faulty_value = self.evaluate_verbose(faulty_in_nets_values)
        logic_value = self.evaluate_verbose(in_nets_values)

        if (faulty_value == None):
            logic_value = None
        elif (logic_value == None):
            faulty_value = None

        return logic_value, faulty_value


    def backtrace(self, expected_out_net_value):
        match self.gate_type:
            case GateType.XOR | GateType.XNOR:
                in_net_x = None
                possible_value = expected_out_net_value
                for in_net in self.in_nets:
                    if (in_net.logic_value == None and in_net.faulty_value == None):
                        if (in_net_x == None):
                            in_net_x = in_net
                    else:
                        possible_value = possible_value ^ in_net.logic_value
                        if self.has_inversion:
                            possible_value = int(not possible_value)
                return (in_net_x, possible_value)
            case _:
                for in_net in self.in_nets:
                    if (in_net.logic_value == None and in_net.faulty_value == None):
                        return (in_net, expected_out_net_value ^ self.has_inversion)


    def all_inputs_assigned(self):
        result = True
        for i in range(0, len(self.in_nets)):
            result = result and self.in_nets[i].assigned
        return result
    

    def perform_fault_list_propagation(self):
        self.evaluate()
        
        # Check with output
        matching_stuck_at_value = int(not self.out_net.logic_value)
        if (matching_stuck_at_value in self.out_net.stuck_at_values):
            self.out_net.faults.add((self.out_net.name, matching_stuck_at_value))
            
        # Propagate inputs' faults
        propagated_faults = set()
        match self.gate_type:
            case GateType.XOR | GateType.XNOR:
                if len(self.in_nets) != 2:
                    print("XOR or XNOR with 2 inputs only is supported in fault simulation")
                    return False
                inputs_faults_union = self.in_nets[0].faults.union(self.in_nets[1].faults)
                inputs_faults_intersection = self.in_nets[0].faults.intersection(self.in_nets[1].faults)
                propagated_faults = inputs_faults_union.difference(inputs_faults_intersection)
            case _:
                controlling_intersection = None
                noncontrolling_union = set()
                has_controlling_input = False

                for in_net in self.in_nets:
                    if in_net.logic_value in self.controlling_values:
                        has_controlling_input = True
                        controlling_intersection = in_net.faults if controlling_intersection is None else controlling_intersection.intersection(in_net.faults)
                    else:
                        noncontrolling_union = noncontrolling_union.union(in_net.faults)

                propagated_faults = controlling_intersection.difference(noncontrolling_union) if has_controlling_input else noncontrolling_union
        
        self.out_net.faults = self.out_net.faults.union(propagated_faults)
        return True