class Net:
    def __init__(self, name: int):
        self.name = name
        
        self.des_gates = []
        self.src_gate = None
        
        self.logic_value = None
        self.faulty_value = None
        self.assigned = False
        self.is_fault_activated = False

        self.stuck_at_values = set()
        self.faults = set()

    def __repr__(self):
        return f"net {self.name}"