from dash import Dash
import dash_bootstrap_components as dbc

import os
assets_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'assets')
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], assets_folder=assets_path)
app.title = "PrAF Evaluator"

# Expose server for generic WSGI usage if needed
server = app.server
