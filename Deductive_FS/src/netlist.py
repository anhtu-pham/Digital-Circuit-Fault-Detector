from gate import Gate, GateType
from net import Net

class Netlist:
    def __init__(self):
        self.gates = []
        self.input_nets = []
        self.output_nets = []
        self.nets_by_name = {}

    def add_line_info(self, line_info: list[str]):
        identifier = line_info[0]
        match identifier:
            case "INPUT":
                for i in range(1, len(line_info) - 1):
                    net_name = int(line_info[i])
                    in_net = self.nets_by_name.setdefault(net_name, Net(net_name))
                    self.input_nets.append(in_net)
            case "OUTPUT":
                for i in range(1, len(line_info) - 1):
                    net_name = int(line_info[i])
                    out_net = self.nets_by_name.setdefault(net_name, Net(net_name))
                    self.output_nets.append(out_net)
            case _:
                try:
                    current_gate = Gate(GateType[identifier])

                    in_nets = []
                    for i in range(1, len(line_info) - 1):
                        in_net_name = int(line_info[i])
                        in_net = self.nets_by_name.setdefault(in_net_name, Net(in_net_name))
                        in_net.des_gates.append(current_gate)
                        in_nets.append(in_net)
                    
                    out_net_name = int(line_info[len(line_info) - 1])
                    out_net = self.nets_by_name.setdefault(out_net_name, Net(out_net_name))
                    out_net.src_gate = current_gate

                    current_gate.set_connecting_nets(in_nets, out_net)
                    self.gates.append(current_gate)

                except ValueError:
                    print("Unknown identifier")

    def build_from_file(self, netlist_filepath: str):
        with open(netlist_filepath, "r") as file:
            print(f"\nStart building netlist from file {netlist_filepath}")
            for line in file:
                line_info = line.strip().split()
                if (len(line_info) > 0):
                    self.add_line_info(line_info)
            print("Completed building netlist\n\n")