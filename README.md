# PrAF Evaluator

A (vibe coded) Python web application for evaluating **Probabilistic Argumentation Frameworks (PrAFs)**. This tool allows users to graphically design argumentation frameworks, assign probabilities to arguments, and evaluate them under various semantics.

## Features

- **Graphical Interface**: Interactive canvas to draw arguments (nodes) and attacks (edges).
- **Probabilistic Support**: Assign probabilities (0-1) to arguments.
- **Semantics Evaluation**: Support for:
  - Grounded
  - Preferred (Credulous/Skeptical)
  - Stable (Credulous/Skeptical)
- **Monte-Carlo Simulation**: efficiently approximates probabilities for complex graphs.
- **Visual Results**: Displays IN/OUT/UNDEC probabilities for each argument.
- **Persistence**: Save and load graph structures.

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository_url>
   cd probabilisticShape
   ```

2. **Create a virtual environment** (recommended):
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. **Run the application**:
   ```bash
   python src/main.py
   ```

2. **Open your browser**:
   Navigate to [http://127.0.0.1:8050/](http://127.0.0.1:8050/).

3. **Interact with the Graph**:
   - **Add Node**: Click on the canvas (outside existing nodes).
   - **Add Edge**: Drag from one node to another.
   - **Edit Node**: Click on a node to change its name or probability.
   - **Delete**: Select a node or edge and press the delete button (if available) or use the interface controls.

4. **Evaluate**:
   - Select the desired semantics from the dropdown.
   - Click "Evaluate" to see the probability of each argument being IN, OUT, or UNDEC.

## Testing

To run the automated tests:

```bash
pytest
```

## Project Structure

- `src/`: Source code for the application.
  - `backend/`: Semantics engine and graph logic.
  - `frontend/`: Dash application layout and callbacks.
- `tests/`: Automated tests.
