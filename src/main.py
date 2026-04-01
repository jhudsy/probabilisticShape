import sys
import os

# Ensure project root is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.frontend.app import app, server
from src.frontend.layout import layout
from src.frontend.callbacks import register_callbacks

app.layout = layout
register_callbacks()

if __name__ == "__main__":
    app.run(debug=True, port=8050)
