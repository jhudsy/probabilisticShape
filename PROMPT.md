I want to create a python web application which can evaluate probabilistic argumentation frameworks.

## Requirements:
- Web based and graphical interface: the user will draw a graph with nodes and edges. Each node will have a label (the name of the argument) and a probability (a number between 0 and 1). The edges will represent attacks between arguments. Edges will be directed. The user will be able to drag and drop nodes and edges to create the graph. Self loops are allowed. Since the graph will be displayed on a canvas, panning and zooming as well as changing node positions will be supported as will creation and deletion of nodes and edges. 
- The user will be able to select a semantics under which to evaluate the graph. The semantics will be selected from grounded, preferred and stable. In addition, if preferred or stable is selected the user will select whether the semantics are credulous or skeptical.
- The application will provide the probability of each argument being IN/OUT/UNDEC under the selected semantics. This will appear as a triple below each argument to 2 decimal places, e.g., 0.31/0.52/0.17. 
- The user will be able to save the current graph structure to a file, load a graph from a file, and export the current canvas as an image. 

## PrAF semantics

PrAF semantics are defined in terms of abstract argumentation frameworks (AFs). An AF is a pair (A, att) where A is a set of arguments and att is a binary relation on A representing attacks. A probabilistic argumentation framework (PrAF) is a pair (A, att, p) where A is a set of arguments, att is a binary relation on A representing attacks, and p is a probability function on A. 
The semantics work on the idea of inducing subgraphs. An induced subgraph is a subgraph which contains a subset of nodes and edges of the original graph and has an associated probability. This probability is calculated by multiplying the probabilities of the nodes which appear in the subgraph and further multiplying these by one minus the probability of each node which does not appear in the subgraph. For each of the induced subgraphs we compute the grounded, preferred or stable semantics (and credulous or skeptical versions of the latter two). We will use a labelling based approach, labelling arguments IN, OUT or UNDEC according to the semantics and the final likelihood of an argument being labelled IN/OUT/UNDEC is the sum of the probabilities of all induced subgraphs in which the argument is labelled IN/OUT/UNDEC according to the selected semantics.

## Labellings
Given a graph G = (A, att) and a labelling L : A -> {IN, OUT, UNDEC}, L is a legal labelling if it satisfies the following conditions:
- An argument is labelled IN if all its attackers are labelled OUT (or if it has no attackers).
- An argument is labelled OUT if it has at least one attacker which is labelled IN.
- An argument is labelled UNDEC if it has no attackers which are labelled IN and it has at least one attacker which is labelled UNDEC.

The grounded labelling is the unique labelling which is maximal with respect to the number of arguments labelled UNDEC
The preferred labelling is the labelling which is maximal with respect to the number of arguments labelled IN
The stable labelling is the labelling which has no arguments labelled UNDEC

We may have multiple preferred and stable labellings. We will thus need to potentially compute the powerset of the set of arguments and compute the semantics for each induced subgraph. Given that this is computationally intensive we should have a progress bar. If we can find existing libraries to compute the labellings efficiently we should use them. 


## Implementation Details

There is a combinatorial explosion of induced subgraphs, so we cannot compute the semantics for each induced subgraph directly. Instead, we will use monte-carlo sampling to approximate the probabilities. We will sample a number of induced subgraphs (defaulting to 10000) and compute the semantics for each using a CSP solver (e.g., `python-constraint`) to efficiently find extensions. We will then average the probabilities of each argument being labelled IN/OUT/UNDEC across all samples. The number of samples will be configurable by the user. 

Since we are using python we will use the `networkx` library to represent the graph and compute the semantics. We will use `plotly` to create the web interface. 
