import networkx as nx
from typing import Set, Dict, List, Tuple
from constraint import Problem, FunctionConstraint
from .af import ArgumentationFramework

def build_graph(af: ArgumentationFramework) -> nx.DiGraph:
    G = nx.DiGraph()
    for arg_id in af.arguments:
        G.add_node(arg_id)
    for attacker, attacked in af.attacks:
        G.add_edge(attacker, attacked)
    return G

def get_grounded_extension(af: ArgumentationFramework) -> Set[str]:
    """
    Computes the grounded extension using standard fixed point.
    Grounded is unique and efficiently computable, so CSP is overkill,
    but we can keep the efficient implementation.
    """
    in_set = set()
    
    def characteristic_function(S: Set[str]) -> Set[str]:
        new_S = set()
        for A in af.arguments:
            attackers = af.get_attackers(A)
            # A is acceptable w.r.t S if all attackers are attacked by S
            is_acceptable = True
            for B in attackers:
                # Is B attacked by S?
                b_attacked_by_S = False
                for C in af.get_attackers(B):
                    if C in S:
                        b_attacked_by_S = True
                        break
                if not b_attacked_by_S:
                    is_acceptable = False
                    break
            if is_acceptable:
                new_S.add(A)
        return new_S

    current_S = set()
    while True:
        next_S = characteristic_function(current_S)
        if next_S == current_S:
            break
        current_S = next_S
        
    return current_S

def get_stable_extensions(af: ArgumentationFramework) -> List[Set[str]]:
    """
    Computes stable extensions using CSP.
    S is stable iff:
    1. S is conflict-free.
    2. S attacks all arguments not in S.
    
    CSP Modelling:
    Var X_a in {0, 1} (1=IN, 0=OUT) for each arg a.
    Constraints:
    - Conflict Free: if X_a=1 and X_b=1 -> not (a attacks b)
    - Attack: if X_a=0 -> exists b in S s.t. b attacks a.
      Equivalent: if X_a=0 -> Sum(X_b for b in attackers(a)) >= 1.
    """
    problem = Problem()
    args = list(af.arguments.keys())
    
    if not args:
        return [set()]

    for arg in args:
        problem.addVariable(arg, [0, 1])
        
    # Constraint 1: Conflict Free
    # For every attack A->B, we cannot have both A=1 and B=1
    for attacker, attacked in af.attacks:
        # Constraint: not (attacker=1 and attacked=1)
        problem.addConstraint(lambda a, b: not (a==1 and b==1), (attacker, attacked))
        
    # Constraint 2: Stability (External Stability)
    # If A is OUT (0), it must be attacked by at least one IN argument.
    # Note: If A is IN (1), it must NOT be attacked by any IN argument (covered by Conflict Free).
    for arg in args:
        attackers = af.get_attackers(arg)
        if not attackers:
            # If no attackers, must be IN (since if OUT, needs attacker IN, which is impossible)
            problem.addConstraint(lambda a: a==1, (arg,))
        else:
            # if a=0 => sum(attackers) >= 1
            # We pass (arg, *attackers) to the lambda
            # Variables involved: arg, att1, att2...
            # Note: capturing 'attackers' in loop needs care? No, addConstraint uses values.
            # Lambda must accept N arguments.
            pass
            
    # Python-constraint generic constraint for Stability
    for arg in args:
        attackers = af.get_attackers(arg)
        if attackers:
            def stability_constraint(val_arg, *val_attackers):
                if val_arg == 1:
                    return True # Handled by conflict free
                # If val_arg == 0, at least one attacker must be 1
                return sum(val_attackers) >= 1
            
            problem.addConstraint(stability_constraint, (arg, *attackers))
            
    solutions = problem.getSolutions()
    extensions = []
    for sol in solutions:
        ext = {arg for arg, val in sol.items() if val == 1}
        extensions.append(ext)
        
    return extensions

def get_preferred_extensions(af: ArgumentationFramework) -> List[Set[str]]:
    """
    Computes preferred extensions using CSP.
    Preferred = Maximal Admissible Set.
    
    Admissible:
    1. Conflict-Free.
    2. Defends itself: If B attacks A (in S), then S attacks B.
    
    CSP Modelling for Admissible:
    Var X_a in {0, 1}.
    - Conflict Free.
    - Defense: If X_a=1, then for all B attacking A, there exists C attacking B with X_c=1.
    """
    problem = Problem()
    args = list(af.arguments.keys())
    
    if not args:
        return [set()]

    for arg in args:
        problem.addVariable(arg, [0, 1])
        
    # Constraint 1: Conflict Free
    for attacker, attacked in af.attacks:
        problem.addConstraint(lambda a, b: not (a==1 and b==1), (attacker, attacked))
        
    # Constraint 2: Defense
    # If A=1, then for each attacker B of A, sum(attackers(B) in S) >= 1.
    for arg in args:
        attackers = af.get_attackers(arg)
        for attacker in attackers:
            # 'attacker' attacks 'arg'.
            # If 'arg' is IN, 'attacker' must be attacked by S.
            defenders = af.get_attackers(attacker)
            
            if not defenders:
                # If unattacked attacker exists, A cannot be IN (unless A doesn't exist? No A is arg).
                # If B attacks A and B has no attackers, A cannot be defended against B.
                # So A must be 0.
                problem.addConstraint(lambda a: a==0, (arg,))
            else:
                # Constraint: if arg=1 => sum(defenders) >= 1
                def defense_constraint(val_arg, *val_defenders):
                    if val_arg == 0:
                        return True
                    return sum(val_defenders) >= 1
                
                problem.addConstraint(defense_constraint, (arg, *defenders))
                
    solutions = problem.getSolutions()
    
    # Filter for maximal sets
    admissible_sets = []
    for sol in solutions:
        admissible_sets.append({arg for arg, val in sol.items() if val == 1})
        
    if not admissible_sets:
        return [set()]
        
    # Find maximal
    preferred = []
    # Sort by size desc to optimize
    admissible_sets.sort(key=len, reverse=True)
    
    for S in admissible_sets:
        is_subset = False
        for P in preferred:
            if S.issubset(P):
                is_subset = True
                break
        if not is_subset:
            # Check against other candidates? 
            # Since we iterate generic list, need to check all bigger/equal ones.
            # But we build 'preferred' incrementally.
            # Actually, standard check: is there any OTHER admissible set T s.t. S subset T (strict)?
            # Since we process large to small, if S is subset of any ALREADY processed P, it's not preferred.
            # Whot about S subset of T where T is yet to be processed? Impossible due to sort.
            # So, check if S is subset of any existing rigid preferred.
            preferred.append(S)
            
    return preferred

def labeling_from_extension(af: ArgumentationFramework, extension: Set[str], semantics_type: str) -> Dict[str, str]:
    labels = {}
    for arg in af.arguments:
        labels[arg] = "UNDEC"
    for arg in extension:
        labels[arg] = "IN"
    for arg in af.arguments:
        if labels[arg] == "IN":
            continue
        attackers = af.get_attackers(arg)
        if any(labels[attacker] == "IN" for attacker in attackers):
            labels[arg] = "OUT"
    return labels

def get_labelings(af: ArgumentationFramework, semantics: str) -> List[Dict[str, str]]:
    if semantics == "grounded":
        ext = get_grounded_extension(af)
        return [labeling_from_extension(af, ext, "grounded")]
    elif semantics == "preferred":
        exts = get_preferred_extensions(af)
        return [labeling_from_extension(af, ext, "preferred") for ext in exts]
    elif semantics == "stable":
        exts = get_stable_extensions(af)
        return [labeling_from_extension(af, ext, "stable") for ext in exts]
    else:
        raise ValueError(f"Unknown semantics: {semantics}")
