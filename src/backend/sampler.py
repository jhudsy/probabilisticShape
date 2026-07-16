import random
from typing import Dict, List, Tuple
from collections import defaultdict
from .af import ArgumentationFramework, Argument
from .semantics import get_labelings

class MonteCarloSampler:
    def __init__(self, af: ArgumentationFramework, num_samples: int = 1000):
        self.af = af
        self.num_samples = num_samples

    def run(self, semantics: str, credulous: bool = True) -> Dict[str, Tuple[float, float, float]]:
        """
        Runs Monte-Carlo simulation.
        Returns a dict mapping argument ID to (P(IN), P(OUT), P(UNDEC)).
        
        If multiple extensions exist (Preferred/Stable), we need to handle credulous/skeptical.
        """
        
        counts = defaultdict(lambda: {"IN": 0, "OUT": 0, "UNDEC": 0})
        
        for _ in range(self.num_samples):
            # 1. Sample induced subgraph
            induced_nodes = []
            for arg_id, arg in self.af.arguments.items():
                if random.random() <= arg.probability:
                    induced_nodes.append(arg)
            
            # Create temporary AF for this subgraph
            sub_af = ArgumentationFramework()
            node_ids = set()
            for arg in induced_nodes:
                sub_af.add_argument(arg)
                node_ids.add(arg.id)
            
            for attacker, attacked in self.af.attacks:
                if attacker in node_ids and attacked in node_ids:
                    sub_af.add_attack(attacker, attacked)
            
            # 2. Compute labelings
            
            labelings = get_labelings(sub_af, semantics)
            
            # Determine status for each PRESENT argument
            for arg_id in node_ids:
                status = "UNDEC" # Default
                
                if not labelings:
                    # No extensions found (e.g. stable semantics with odd cycle)
                    # so counts stay 0.
                    pass
                else:
                    if credulous:
                        # Credulous: X if X in ANY extension
                        is_in = False
                        is_out = False
                        is_undec = False
                        
                        for lab in labelings:
                            status = lab[arg_id]
                            if status == "IN": is_in = True
                            if status == "OUT": is_out = True
                            if status == "UNDEC": is_undec = True
                        
                        if is_in: counts[arg_id]["IN"] += 1
                        if is_out: counts[arg_id]["OUT"] += 1
                        if is_undec: counts[arg_id]["UNDEC"] += 1
                            
                    else:
                        # Skeptical: X if X in ALL extensions
                        all_in = True
                        all_out = True
                        all_undec = True
                        
                        for lab in labelings:
                            status = lab[arg_id]
                            if status != "IN": all_in = False
                            if status != "OUT": all_out = False
                            if status != "UNDEC": all_undec = False
                            
                        if all_in: counts[arg_id]["IN"] += 1
                        if all_out: counts[arg_id]["OUT"] += 1
                        if all_undec: counts[arg_id]["UNDEC"] += 1

        # Normalize
        results = {}
        for arg_id in self.af.arguments:
            res = counts[arg_id]
            # If argument never appeared, it will be 0,0,0
            results[arg_id] = (
                res["IN"] / self.num_samples,
                res["OUT"] / self.num_samples,
                res["UNDEC"] / self.num_samples
            )
            
        return results
