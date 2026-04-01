from dash import dcc, html
import dash_cytoscape as cyto
import dash_bootstrap_components as dbc

# Define styles for the graph
default_stylesheet = [
    {
        'selector': 'node',
        'style': {
            'background-color': '#007bff',
            'content': 'data(label)',
            'color': 'white',
            'font-size': '12px',
            'width': '100px',
            'height': '40px',
            'shape': 'round-rectangle',
            'text-valign': 'center',
            'text-halign': 'center',
            'text-wrap': 'wrap'
        }
    },
    {
        'selector': 'edge',
        'style': {
            'curve-style': 'bezier',
            'target-arrow-shape': 'triangle',
            'line-color': '#ccc',
            'target-arrow-color': '#ccc'
        }
    },
    {
        'selector': ':selected',
        'style': {
            'background-color': '#dc3545',
            'line-color': '#dc3545',
            'target-arrow-color': '#dc3545',
            'border-width': '2px',
            'border-color': '#28a745'
        }
    }
]

layout = dbc.Container([
    dbc.Row([
        dbc.Col(html.H1("PrAF Evaluation Framework"), className="my-3")
    ]),
    dbc.Row([
        # Sidebar Controls
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Controls"),
                dbc.CardBody([
                    html.H5("File Operations"),
                    dbc.Row([
                        dbc.Col(dcc.Upload(
                            id='upload-graph',
                            children=dbc.Button("Load JSON", color="info", size="sm", className="w-100"),
                            multiple=False
                        ), width=6),
                        dbc.Col(dbc.Button("Save JSON", id="btn-save", color="info", size="sm", className="w-100"), width=6),
                    ], className="mb-2"),
                    dbc.Button("Export Image", id="btn-export-img", color="dark", size="sm", className="w-100 mb-3"),
                    dcc.Download(id="download-graph"),
                    
                    dbc.Button("Generate Random Graph", id="btn-open-gen-modal", color="secondary", size="sm", className="w-100 mb-3"),
                    
                    html.Hr(),
                    html.H5("Edit Graph"),
                    dbc.Button("Add Argument", id="btn-add-node", color="primary", size="sm", className="me-1 mb-2"),
                    dbc.Button("Add Attack (Select src, tgt)", id="btn-add-edge", color="secondary", size="sm", className="mb-2"),
                    dbc.Button("Delete Selected", id="btn-delete", color="danger", size="sm", className="mb-2"),
                    
                    html.Hr(),
                    html.H5("Node Properties"),
                    dbc.Label("Name"),
                    dbc.Input(id="input-node-name", type="text", placeholder="Select a node...", disabled=True),
                    dbc.Label("Probability (0.0 - 1.0)", className="mt-2"),
                    dbc.Input(id="input-node-prob", type="number", min=0, max=1, step=0.01, placeholder="Select a node...", disabled=True),
                    dbc.Button("Update Node", id="btn-update-node", color="success", size="sm", className="mt-2"),
                    
                    html.Hr(),
                    html.H5("Evaluation"),
                    dbc.Label("Semantics"),
                    dcc.Dropdown(
                        id="dropdown-semantics",
                        options=[
                            {'label': 'Grounded', 'value': 'grounded'},
                            {'label': 'Preferred', 'value': 'preferred'},
                            {'label': 'Stable', 'value': 'stable'}
                        ],
                        value='grounded',
                        clearable=False
                    ),
                    
                    html.Div([
                        dbc.Label("Mode", className="mt-2"),
                        dbc.RadioItems(
                            id="radio-mode",
                            options=[
                                {'label': 'Credulous', 'value': 'credulous'},
                                {'label': 'Skeptical', 'value': 'skeptical'}
                            ],
                            value='credulous',
                            inline=True
                        )
                    ], id="div-mode-controls", style={'display': 'none'}), # Hidden for grounded
                    
                    dbc.Label("Monte-Carlo Samples", className="mt-2"),
                    dbc.Input(id="input-samples", type="number", value=1000, step=100),
                    
                    dbc.Button("Run Evaluation", id="btn-run", color="warning", size="lg", className="mt-3 w-100"),
                ])
            ], className="h-100")
        ], width=3),
        
        # Main Canvas
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Graph Editor"),
                dbc.CardBody([
                    html.Div([
                        cyto.Cytoscape(
                            id='cytoscape-graph',
                            layout={'name': 'preset'},
                            style={'width': '100%', 'height': '600px'},
                            elements=[],
                            stylesheet=default_stylesheet,
                            userZoomingEnabled=True,
                            userPanningEnabled=True,
                            responsive=True,
                            zoom=0.5,
                            pan={'x': 200, 'y': 200}
                        )
                    ], id='graph-wrapper', style={'height': '100%', 'width': '100%'})
                ])
            ])
        ], width=9)
    ]),
    
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Results"),
                dbc.CardBody(id="results-area", children="Run evaluation to see results.")
            ], className="mt-3")
        ])
    ]),
    dcc.Store(id='store-edge-creation', data={'step': 'idle', 'source_id': None}),
    dcc.Store(id='store-evaluation-results', data={}),
    
    # Random Graph Generation Modal
    dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle("Generate Random Graph")),
        dbc.ModalBody([
            dbc.Label("Number of Arguments"),
            dbc.Input(id="input-gen-nodes", type="number", value=5, min=1, step=1),
            html.Br(),
            dbc.Label("Number of Attacks"),
            dbc.Input(id="input-gen-edges", type="number", value=8, min=0, step=1),
            html.Br(),
            dbc.Label("Generator algorithm"),
            dcc.Dropdown(
                id="dropdown-gen-algo",
                options=[{'label': 'GNM Random Graph', 'value': 'gnm'}],
                value='gnm',
                clearable=False
            )
        ]),
        dbc.ModalFooter([
            dbc.Button("Cancel", id="btn-gen-cancel", className="ms-auto", n_clicks=0),
            dbc.Button("Generate", id="btn-gen-confirm", color="primary", n_clicks=0, className="ms-2"),
        ]),
    ], id="modal-generate", is_open=False)
], fluid=True)
