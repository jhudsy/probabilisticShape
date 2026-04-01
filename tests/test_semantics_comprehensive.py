import pytest
from src.backend.af import Argument, ArgumentationFramework
from src.backend.semantics import get_grounded_extension, get_preferred_extensions, get_stable_extensions
from src.backend.sampler import MonteCarloSampler

# --- Helper Functions ---
def create_af(attacks):
    """
    Creates an AF from a list of attacks (tuples).
    Arguments are inferred from attacks.
    """
    af = ArgumentationFramework()
    args = set()
    for att in attacks:
        args.add(att[0])
        args.add(att[1])
    for arg_name in args:
        af.add_argument(Argument(arg_name, arg_name, 1.0))
    for att in attacks:
        af.add_attack(att[0], att[1])
    return af

def check_extensions(computed, expected):
    """
    Checks if computed list of sets matches expected list of sets (order independent).
    """
    assert len(computed) == len(expected)
    computed_sorted = sorted([sorted(list(s)) for s in computed])
    expected_sorted = sorted([sorted(list(s)) for s in expected])
    assert computed_sorted == expected_sorted

# --- Test Cases ---

def test_grounded_chain():
    # A -> B -> C
    af = create_af([("A", "B"), ("B", "C")])
    ext = get_grounded_extension(af)
    assert ext == {"A", "C"}

def test_grounded_floating():
    # A -> B, B -> A, A -> C, B -> C
    af = create_af([("A", "B"), ("B", "A"), ("A", "C"), ("B", "C")])
    ext = get_grounded_extension(af)
    assert ext == set() # Empty

def test_preferred_floating():
    # A -> B, B -> A, A -> C, B -> C
    # Extensions: {A}, {B}.
    # Note: {A} attacks B and C. Conflict free. Admissible. Maximal.
    # Note: {B} attacks A and C. Conflict free. Admissible. Maximal.
    af = create_af([("A", "B"), ("B", "A"), ("A", "C"), ("B", "C")])
    exts = get_preferred_extensions(af)
    check_extensions(exts, [{"A"}, {"B"}])

def test_stable_floating():
    # A -> B, B -> A, A -> C, B -> C
    # {A}: Attacks B (in graph), Attacks C. Valid stable.
    # {B}: Attacks A, Attacks C. Valid stable.
    af = create_af([("A", "B"), ("B", "A"), ("A", "C"), ("B", "C")])
    exts = get_stable_extensions(af)
    check_extensions(exts, [{"A"}, {"B"}])

def test_preferred_odd_cycle_plus():
    # A -> B -> C -> A. And A -> D.
    # Cycle has no preferred extension other than empty?
    # Actually, empty set is admissible.
    # Is it maximal? Yes, if no non-empty admissible set exists.
    # {D}?? C attacks A. A attacks D.
    # If {D}, must defend D. A attacks D. So must attack A. C attacks A.
    # So {C, D}?
    # C attacks A. A attacks B. B attacks C.
    # Is {C, D} conflict free? Yes.
    # Does it defend itself?
    # C is attacked by B. Who attacks B? A. Is A in {C, D}? No.
    # So {C, D} is not admissible.
    # So likely only empty set is admissible.
    
    af = create_af([("A", "B"), ("B", "C"), ("C", "A"), ("A", "D")])
    exts = get_preferred_extensions(af)
    check_extensions(exts, [set()])

def test_stable_odd_cycle_plus():
    # A -> B -> C -> A. A -> D.
    # No stable extension.
    af = create_af([("A", "B"), ("B", "C"), ("C", "A"), ("A", "D")])
    exts = get_stable_extensions(af)
    check_extensions(exts, [])

def test_skeptical_credulous_acceptance():
    # Using Sampler logic (with 100% probs) to verify skeptical/credulous
    # Floating: {A}, {B}. C attacked by both.
    # Credulous: A (Yes), B (Yes), C (No - never IN).
    # Skeptical: A (No - not in all), B (No), C (No).
    
    af = create_af([("A", "B"), ("B", "A"), ("A", "C"), ("B", "C")])
    sampler = MonteCarloSampler(af, num_samples=10) # Deterministic graph
    
    # Preferred Credulous
    res_cred = sampler.run("preferred", credulous=True)
    # A: IN=100%
    assert res_cred["A"][0] == 1.0
    # B: IN=100%
    assert res_cred["B"][0] == 1.0
    # C: IN=0%
    assert res_cred["C"][0] == 0.0
    
    # Preferred Skeptical
    res_skep = sampler.run("preferred", credulous=False)
    # A: IN=0% (In one but not other)
    assert res_skep["A"][0] == 0.0
    # B: IN=0%
    assert res_skep["B"][0] == 0.0
    # C: IN=0%
    assert res_skep["C"][0] == 0.0

def test_nixon_diamond_skeptical():
    # Nixon Diamond: A -> C, B -> C, A -> B (Cycle? No, A and B mutually attack in standard, but here let's make A, B unattacked?)
    # Classic Nixon: A (Quaker), B (Republican). Both attack C (Pacifist).
    # Usually A -> not C, B -> C. Mutual attack or similar.
    # Let's simple mutual attack A-B, both attack C. (Floating-like).
    # Tested above.
    pass

def test_four_cycle():
    # A -> B -> C -> D -> A
    # Even cycle.
    # Sets: {A, C}, {B, D}.
    af = create_af([("A", "B"), ("B", "C"), ("C", "D"), ("D", "A")])
    
    # Grounded: {}
    assert get_grounded_extension(af) == set()
    
    # Preferred: {A, C}, {B, D}
    exts = get_preferred_extensions(af)
    check_extensions(exts, [{"A", "C"}, {"B", "D"}])
    
    # Stable: {A, C}, {B, D}
    exts_st = get_stable_extensions(af)
    check_extensions(exts_st, [{"A", "C"}, {"B", "D"}])
