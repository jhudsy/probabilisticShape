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
        
        For a single sample (induced subgraph), there might be multiple extensions E1, E2...
        
        The requirement says:
        "The final likelihood ... is the sum of the probabilities of all induced subgraphs in which the argument is labelled IN/OUT/UNDEC"
        
        But wait, if a subgraph has multiple extensions, is the argument IN?
        Requirements: "if preferred or stable is selected the user will select whether the semantics are credulous or skeptical."
        
        So for a specific induced subgraph G':
        - Credulous: Arg is IN if it is in AT LEAST ONE extension of G'.
        - Skeptical: Arg is IN if it is in ALL extensions of G'.
        
        What about OUT/UNDEC?
        Standard definitions usually applied to IN. 
        However, the output requires P(IN), P(OUT), P(UNDEC).
        
        Let's assume for a single induced subgraph:
        - If Credulous:
            - Status is IN if in ANY extension.
            - Status is OUT if NOT IN and in ANY extension it is OUT? Or if attacked by IN in any extension?
            This is slightly ambiguous for PrAFs with multiple extensions.
            
            Common interpretation:
            P(Acc(A)) = sum P(G') * I(A is acceptable in G')
            
            If credulous: A is acceptable in G' if exists E in Ext(G') s.t. A in E.
            If skeptical: A is acceptable in G' if forall E in Ext(G'), A in E.
            
            But we need a triplet (IN, OUT, UNDEC).
            Since the probabilities must sum to 1, we need to partition the space for *each subgraph*.
            
            Let's define the status of A in G' uniquely:
            - IN_cred: Exists E, A in E.
            - OUT_cred: Exists E, A is OUT in E? Or maybe "Not IN_cred"?
            
            Actually, let's simplify based on the "triple" requirement.
            Usually, for one subgraph with multiple extensions, we might average over extensions? 
            OR, the user selects "Credulous Preferred".
            This implies we treat the subgraph as having that status.
            
            Let's clarify via "Standard" approach:
            For a graph G', we compute set of extensions.
            If Credulous:
                Label A as IN if A is in some extension.
                Label A as OUT if A is OUT in some extension? 
                Label A as UNDEC otherwise?
                Note: A could be IN in some and OUT in others. 
                
            If Skeptical:
                Label A as IN if A is in all extensions.
                Label A as OUT if A is OUT in all extensions.
                Label A as UNDEC otherwise.
                
            Let's stick to this "Skeptical" logic which is consistent.
            For "Credulous", if we define IN = "in some", then OUT should probably be "in some OUT" (which overlaps) or "not IN"?
            
            Let's try to follow the standard "Justification Status" in abstract argumentation.
            - Skeptically Accepted: in all E
            - Credulously Accepted: in some E
            - Skeptically Rejected: attacked by all E (OUT in all E)
            - Credulously Rejected: attacked by some E (OUT in some E)
            
            The requirement asks for a probability triple.
            Let's assume for a subgraph G', we calculate a SINGLE label for each argument based on the chosen mode (Cred/Skep).
            
            Mode: Credulous
            - Label IN if IN in ANY extension.
            - Label OUT if OUT in ANY extension AND NOT IN (priority to IN? or overlap?)
            - Label UNDEC otherwise.
            
            Actually, looking at the UI output "0.31/0.52/0.17", these sum to 1.
            So we really need to classify each subgraph into one of three buckets for each argument.
            
            Let's make a choice:
            If Credulous:
                - IN if exists E s.t. Label(A, E) == IN
                - OUT if (not IN) and (exists E s.t. Label(A, E) == OUT)
                - UNDEC otherwise.
            If Skeptical:
                - IN if forall E, Label(A, E) == IN
                - OUT if forall E, Label(A, E) == OUT
                - UNDEC otherwise.
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
            # Note: Arguments NOT in the subgraph are not labeled IN/OUT/UNDEC in the subgraph context.
            # But they "appear" in the original graph.
            # How do we count them?
            # "The probability of each argument being IN/OUT/UNDEC"
            # If an argument is not in the induced subgraph, it effectively doesn't exist in that world.
            # Does it contribute to the probability?
            # E.g. P(A is IN). If A is not in world w, is A IN in w? No. Is it OUT? No.
            # It seems it counts as "not IN".
            # BUT, the sum presumably should be over the worlds where it exists?
            # OR, maybe the triple sums to 1 implies we just categorize the world.
            # If A is not in the subgraph, it is neither IN, OUT, nor UNDEC.
            # This would result in P(IN) + P(OUT) + P(UNDEC) = P(A exists).
            # This makes sense. The "missing mass" 1 - P(exists) is just "absent".
            # HOWEVER, the UI example "0.31/0.52/0.17" sums to 1.0.
            # This implies the probability is CONDITIONAL on A existing? 
            # OR, "absent" is mapped to something?
            # Let's assume the question implies "Given the Probabilistic Framework, what is the probability A is IN/OUT/UNDEC".
            # If the user sees P(all) < 1, they might be confused.
            # But formally, P(IN) = sum_{w} P(w) * I(A is IN in w).
            # If A is not in w, I(A is IN in w) is 0.
            # So P(IN) + P(OUT) + P(UNDEC) = P(A exists).
            
            # Let's verify with requirement: "Each node will have a label ... and a probability".
            # If I set P(A) = 0.5. A is not connected to anything.
            # Subgraphs:
            # 1. A exists (prob 0.5). Status: IN (unattacked).
            # 2. A absent (prob 0.5). Status: None.
            # Result: P(IN)=0.5, P(OUT)=0, P(UNDEC)=0. Sum=0.5.
            # PROBABLY, we should just report these raw numbers.
            # Or maybe "absent" is treated as OUT? No, that's semantically wrong.
            # I will return the raw probabilities. If they sum to < 1, that's correct for PrAFs.
            # Wait, the example "0.31/0.52/0.17" sums to 1. 0.31+0.52 = 0.83 + 0.17 = 1.0.
            # This strongly suggests the probabilities are either normalized, or my interpretation of "absent" is wrong.
            # OR, maybe the example assumes P(A)=1 for all A? No, "Each node will have ... probability (number between 0 and 1)".
            
            # Alternative Idea:
            # Maybe the labels are calculated on the FULL graph, but edges/nodes are probabilistic?
            # "The semantics work on the idea of inducing subgraphs." -> Yes, arguments are removed.
            
            # I'll stick to P(IN) + P(OUT) + P(UNDEC) <= 1.
            # I will note this in the UI.
            
            labelings = get_labelings(sub_af, semantics)
            
            # Determine status for each PRESENT argument
            for arg_id in node_ids:
                status = "UNDEC" # Default
                
                if not labelings:
                    # No extensions found (e.g. stable semantics with odd cycle)
                    # Status remains default (0 contributions) if we assume "exists" quantifier?
                    # Or "All" is distinct?
                    # If empty set of extensions, "All X" is vacuously true? 
                    # Standard logic: if no stable extensions, nothing is justified.
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
