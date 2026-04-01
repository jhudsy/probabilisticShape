from dataclasses import dataclass, field
from typing import List, Tuple, Dict, Set, Optional

@dataclass
class Argument:
    id: str
    name: str
    probability: float = 1.0

@dataclass
class ArgumentationFramework:
    arguments: Dict[str, Argument] = field(default_factory=dict)
    attacks: Set[Tuple[str, str]] = field(default_factory=set)

    def add_argument(self, arg: Argument):
        self.arguments[arg.id] = arg

    def add_attack(self, attacker_id: str, attacked_id: str):
        if attacker_id not in self.arguments or attacked_id not in self.arguments:
            raise ValueError("Both arguments must be in the framework before adding an attack.")
        self.attacks.add((attacker_id, attacked_id))
    
    def get_attackers(self, arg_id: str) -> List[str]:
        return [attacker for attacker, attacked in self.attacks if attacked == arg_id]
        
    def get_attacked(self, arg_id: str) -> List[str]:
        return [attacked for attacker, attacked in self.attacks if attacker == arg_id]
