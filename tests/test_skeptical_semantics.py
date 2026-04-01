import pytest
from src.backend.af import Argument, ArgumentationFramework
from src.backend.sampler import MonteCarloSampler

def test_skeptical_preferred_cycle():
    # A <-> B. P(A)=1, P(B)=1.
    # Preferred Extensions: {A}, {B}
    # Skeptical IN: A in All? No. B in All? No.
    # Skeptical OUT: A out in All? No (In in {A}).
    # Skeptical UNDEC: A undec in All? No (In/Out in extensions).
    
    # Expected Result: 0/0/0 for both A and B.
    
    af = ArgumentationFramework()
    af.add_argument(Argument("A", "A", 1.0))
    af.add_argument(Argument("B", "B", 1.0))
    af.add_attack("A", "B")
    af.add_attack("B", "A")
    
    sampler = MonteCarloSampler(af, num_samples=100) # Deterministic graph, so 100 is enough
    
    # We need to ensure we are testing "preferred" and "skeptical" mode.
    # The sampler.run method takes 'semantics' and 'credulous' boolean.
    # Skeptical -> credulous=False
    
    res = sampler.run("preferred", credulous=False)
    
    # Verify A
    assert res["A"][0] == 0.0 # IN
    assert res["A"][1] == 0.0 # OUT
    assert res["A"][2] == 0.0 # UNDEC
    
    # Verify B
    assert res["B"][0] == 0.0
    assert res["B"][1] == 0.0
    assert res["B"][2] == 0.0
