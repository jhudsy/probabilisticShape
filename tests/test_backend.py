import pytest
from src.backend.af import Argument, ArgumentationFramework
from src.backend.semantics import get_grounded_extension, get_preferred_extensions, get_stable_extensions
from src.backend.sampler import MonteCarloSampler

def test_af_structure():
    af = ArgumentationFramework()
    a = Argument("A", "Arg A")
    b = Argument("B", "Arg B")
    af.add_argument(a)
    af.add_argument(b)
    af.add_attack("A", "B")
    
    assert "A" in af.arguments
    assert "B" in af.arguments
    assert ("A", "B") in af.attacks
    assert af.get_attackers("B") == ["A"]

def test_grounded_simple():
    # A -> B
    af = ArgumentationFramework()
    af.add_argument(Argument("A", "A"))
    af.add_argument(Argument("B", "B"))
    af.add_attack("A", "B")
    
    g = get_grounded_extension(af)
    assert "A" in g
    assert "B" not in g

def test_grounded_cycle():
    # A -> B -> A
    af = ArgumentationFramework()
    af.add_argument(Argument("A", "A"))
    af.add_argument(Argument("B", "B"))
    af.add_attack("A", "B")
    af.add_attack("B", "A")
    
    g = get_grounded_extension(af)
    # Grounded should be empty
    assert len(g) == 0

def test_preferred_cycle():
    # A -> B -> A
    af = ArgumentationFramework()
    af.add_argument(Argument("A", "A"))
    af.add_argument(Argument("B", "B"))
    af.add_attack("A", "B")
    af.add_attack("B", "A")
    
    exts = get_preferred_extensions(af)
    # Should be {A}, {B}
    assert len(exts) == 2
    assert {"A"} in exts
    assert {"B"} in exts

def test_stable_cycle():
     # A -> B -> A
    af = ArgumentationFramework()
    af.add_argument(Argument("A", "A"))
    af.add_argument(Argument("B", "B"))
    af.add_attack("A", "B")
    af.add_attack("B", "A")
    
    exts = get_stable_extensions(af)
    # Should be {A}, {B}
    assert len(exts) == 2

def test_stable_odd_cycle():
    # A -> B -> C -> A (no stable ext)
    af = ArgumentationFramework()
    af.add_argument(Argument("A", "A"))
    af.add_argument(Argument("B", "B"))
    af.add_argument(Argument("C", "C"))
    af.add_attack("A", "B")
    af.add_attack("B", "C")
    af.add_attack("C", "A")
    
    exts = get_stable_extensions(af)
    assert len(exts) == 0

def test_sampler_basic():
    # A -> B. P(A)=1, P(B)=1.
    # Grounded: A IN, B OUT.
    af = ArgumentationFramework()
    af.add_argument(Argument("A", "A", 1.0))
    af.add_argument(Argument("B", "B", 1.0))
    af.add_attack("A", "B")
    
    sampler = MonteCarloSampler(af, num_samples=50)
    res = sampler.run("grounded")
    
    # A: IN=1.0, OUT=0, UNDEC=0
    assert res["A"][0] == 1.0
    # B: IN=0, OUT=1.0, UNDEC=0
    assert res["B"][1] == 1.0

def test_sampler_uncertain():
    # A independent. P(A)=0.5.
    af = ArgumentationFramework()
    af.add_argument(Argument("A", "A", 0.5))
    
    sampler = MonteCarloSampler(af, num_samples=1000)
    res = sampler.run("grounded")
    
    # P(IN) should be approx 0.5
    assert 0.4 < res["A"][0] < 0.6
    # P(OUT) should be 0 (never attacked)
    assert res["A"][1] == 0.0
    # P(UNDEC) should be 0 (never undec in grounded here)
    assert res["A"][2] == 0.0
    # Sum approx 0.5 (rest is absence)

