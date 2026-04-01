from dash import Input, Output, State, callback_context, no_update
from dash.exceptions import PreventUpdate
import json
import base64
import uuid
import random
from .app import app
from src.backend.af import ArgumentationFramework, Argument
from src.backend.sampler import MonteCarloSampler

import itertools
import networkx as nx

def generate_id():
    return str(uuid.uuid4())[:8]

def get_next_name(elements):
    existing_names = set()
    for el in elements:
        if 'source' not in el['data']:
            existing_names.add(el['data'].get('name', ''))
    
    chars = "abcdefghijklmnopqrstuvwxyz"
    length = 1
    while True:
        for p in itertools.product(chars, repeat=length):
            name = "".join(p)
            if name not in existing_names:
                return name
        length += 1

def register_callbacks():
    
    @app.callback(
        Output("div-mode-controls", "style"),
        Input("dropdown-semantics", "value")
    )
    def toggle_mode_controls(semantics):
        if semantics == "grounded":
            return {'display': 'none'}
        return {'display': 'block'}

    # EXPORT IMAGE
    @app.callback(
        Output('cytoscape-graph', 'generateImage'),
        Input('btn-export-img', 'n_clicks')
    )
    def export_image(n_clicks):
        if not n_clicks:
            return no_update
        return {
            'type': 'png',
            'action': 'download',
            'filename': 'praf_graph'
        }

    # SAVE GRAPH (Download JSON)
    @app.callback(
        Output("download-graph", "data"),
        Input("btn-save", "n_clicks"),
        State("cytoscape-graph", "elements")
    )
    def save_graph(n_clicks, elements):
        if not n_clicks or not elements:
            return no_update
        return dict(content=json.dumps(elements, indent=2), filename="graph.json")

    # LOAD GRAPH (Upload JSON)
    # AND Manage Graph logic (merged for elements update)
    # Wait, simple callbacks are better. 
    # But `elements` is Output of both Manage logic and Load logic.
    # Dash allows multiple inputs updating same output.
    # So I can put it all in `manage_graph` or have separate callback.
    # If I separate, I need to wrap `elements` in one callback.
    # I will Merge Load into `manage_graph` to avoid "Multiple callbacks targeting same output".

    @app.callback(
        [Output("cytoscape-graph", "elements"),
         Output("store-edge-creation", "data"),
         Output("input-node-name", "value"),
         Output("input-node-prob", "value"),
         Output("input-node-name", "disabled"),
         Output("input-node-prob", "disabled")],
        [Input("btn-add-node", "n_clicks"),
         Input("btn-add-edge", "n_clicks"),
         Input("btn-delete", "n_clicks"),
         Input("btn-update-node", "n_clicks"),
         Input("cytoscape-graph", "tapNode"),
         Input("btn-run", "n_clicks"),
         Input("input-node-name", "n_submit"),
         Input("input-node-prob", "n_submit"),
         Input('upload-graph', 'contents')], # ADDED
        [State("cytoscape-graph", "elements"),
         State("cytoscape-graph", "selectedNodeData"),
         State("cytoscape-graph", "selectedEdgeData"),
         State("cytoscape-graph", "mouseoverNodeData"),
         State("store-edge-creation", "data"),
         State("input-node-name", "value"),
         State("input-node-prob", "value"),
         State("dropdown-semantics", "value"),
         State("radio-mode", "value"),
         State("input-samples", "value")]
    )
    def manage_graph(btn_add, btn_edge, btn_del, btn_update, tap_node, btn_run,
                    submit_name, submit_prob, upload_content,
                    elements, selected_nodes, selected_edges, mouseover_node,
                    edge_state, name_val, prob_val, 
                    semantics, mode, samples):
        
        ctx = callback_context
        if not ctx.triggered:
            return no_update, no_update, no_update, no_update, no_update, no_update
        
        trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
        
        if elements is None:
            elements = []
            
        new_edge_state = edge_state
        
        # 0. Upload Graph
        if trigger_id == "upload-graph":
            if upload_content:
                try:
                    content_type, content_string = upload_content.split(',')
                    decoded = base64.b64decode(content_string)
                    new_elements = json.loads(decoded.decode('utf-8'))
                    return new_elements, {'step': 'idle', 'source_id': None}, "", "", True, True
                except Exception as e:
                    print(e)
                    return no_update, no_update, no_update, no_update, no_update, no_update
            return no_update, no_update, no_update, no_update, no_update, no_update

        # 1. Add Node (Button Only)
        if trigger_id == "btn-add-node":
            new_id = generate_id()
             # Use sequential name
            new_name = get_next_name(elements)
            
            new_node = {
                'data': {'id': new_id, 'label': f"{new_name}\n(P=1.00)", 'name': new_name, 'probability': 1.0},
                'position': {'x': random.randint(100, 500), 'y': random.randint(100, 500)}
            }
            elements.append(new_node)
            return elements, new_edge_state, no_update, no_update, no_update, no_update

        # 2. Add Edge (Button Click - Start Mode)
        if trigger_id == "btn-add-edge":
            new_edge_state = {'step': 'select_source', 'source_id': None}
            return no_update, new_edge_state, no_update, no_update, no_update, no_update

        # 3. Tap Node (Selection OR Edge Creation)
        if trigger_id == "cytoscape-graph":
            if not tap_node:
                return no_update, no_update, "", "", True, True
            
            node_data = tap_node['data']
            node_id = node_data['id']
            
            # Handle Edge Creation
            if edge_state['step'] == 'select_source':
                new_edge_state = {'step': 'select_target', 'source_id': node_id}
                return no_update, new_edge_state, node_data.get('name', ''), node_data.get('probability', 1.0), False, False
                
            elif edge_state['step'] == 'select_target':
                source_id = edge_state['source_id']
                # Allow self-attacks (source_id == node_id is OK now)
                
                # Add edge
                edge_id = f"{source_id}->{node_id}"
                exists = any(e.get('data', {}).get('source') == source_id and e.get('data', {}).get('target') == node_id for e in elements)
                if not exists:
                    elements.append({
                        'data': {'source': source_id, 'target': node_id, 'id': edge_id}
                    })
                new_edge_state = {'step': 'idle', 'source_id': None}
                return elements, new_edge_state, node_data.get('name', ''), node_data.get('probability', 1.0), False, False
            
            else:
                # Just selecting node for editing
                return no_update, no_update, node_data.get('name', ''), node_data.get('probability', 1.0), False, False

        # 4. Update Node (Button OR Enter Key)
        if trigger_id == "btn-update-node" or trigger_id == "input-node-name" or trigger_id == "input-node-prob":
            if not selected_nodes:
                return no_update, no_update, no_update, no_update, no_update, no_update
            
            ids_to_update = [n['id'] for n in selected_nodes]
            for el in elements:
                if 'source' not in el['data'] and el['data']['id'] in ids_to_update:
                     el['data']['name'] = name_val
                     el['data']['probability'] = float(prob_val)
                     el['data']['label'] = f"{name_val}\n(P={float(prob_val):.2f})" 
            
            return elements, no_update, no_update, no_update, no_update, no_update

        # 5. Delete
        if trigger_id == "btn-delete":
            if not selected_nodes and not selected_edges:
                return no_update, no_update, no_update, no_update, no_update, no_update
            
            ids_to_del = set()
            if selected_nodes:
                ids_to_del.update([n['id'] for n in selected_nodes])
            if selected_edges:
                ids_to_del.update([e['id'] for e in selected_edges])
                
            new_elements = []
            for el in elements:
                is_edge = 'source' in el['data']
                if is_edge:
                    if el['data']['id'] in ids_to_del:
                        continue
                    if el['data']['source'] in ids_to_del or el['data']['target'] in ids_to_del:
                        continue
                    new_elements.append(el)
                else:
                    if el['data']['id'] in ids_to_del:
                        continue
                    new_elements.append(el)
            
            return new_elements, no_update, "", "", True, True

        # 6. Run Evaluation
        if trigger_id == "btn-run":
            af = ArgumentationFramework()
            node_map = {} 
            
            for el in elements:
                if 'source' not in el['data']:
                    d = el['data']
                    arg = Argument(d['id'], d.get('name', d['id']), float(d.get('probability', 1.0)))
                    af.add_argument(arg)
                    node_map[d['id']] = d
            
            for el in elements:
                if 'source' in el['data']:
                    src = el['data']['source']
                    tgt = el['data']['target']
                    if src in af.arguments and tgt in af.arguments:
                        af.add_attack(src, tgt)
            
            sampler = MonteCarloSampler(af, num_samples=int(samples or 1000))
            is_cred = (mode == "credulous")
            results = sampler.run(semantics, credulous=is_cred)
            
            for el in elements:
                if 'source' not in el['data']:
                    nid = el['data']['id']
                    if nid in results:
                        p_in, p_out, p_undec = results[nid]
                        name = el['data'].get('name', nid)
                        prob = el['data'].get('probability', 1.0)
                        probs = f"{p_in:.2f}/{p_out:.2f}/{p_undec:.2f}"
                        el['data']['label'] = f"{name}\n(P={prob:.2f})\n{probs}"
                        
            return elements, no_update, no_update, no_update, no_update, no_update

        return no_update, no_update, no_update, no_update, no_update, no_update

    # RANDOM GRAPH MODAL
    @app.callback(
        Output("modal-generate", "is_open"),
        [Input("btn-open-gen-modal", "n_clicks"), Input("btn-gen-cancel", "n_clicks")],
        [State("modal-generate", "is_open")],
    )
    def toggle_modal(n1, n2, is_open):
        if n1 or n2:
            return not is_open
        return is_open

    # RANDOM GRAPH GENERATION
    @app.callback(
        Output("cytoscape-graph", "elements", allow_duplicate=True),
        Input("btn-gen-confirm", "n_clicks"),
        [State("input-gen-nodes", "value"),
         State("input-gen-edges", "value"),
         State("dropdown-gen-algo", "value")],
        prevent_initial_call=True
    )
    def generate_random_graph(n_clicks, n_nodes, n_edges, algo):
        if not n_clicks:
            return no_update
        
        # Generator
        if algo == 'gnm':
             try:
                G = nx.gnm_random_graph(n_nodes, n_edges, directed=True)
             except Exception as e:
                print(f"Error generating graph: {e}")
                return no_update
        else:
             G = nx.gnm_random_graph(n_nodes, n_edges, directed=True)

        # Layout
        try:
            pos = nx.spring_layout(G, scale=400, center=(300, 300))
        except:
            pos = {}

        new_elements = []
        
        # Name generator helper
        def num_to_name(n):
            chars = "abcdefghijklmnopqrstuvwxyz"
            if n < 26:
                return chars[n]
            return chars[n // 26 - 1] + chars[n % 26] # Simple fallback
            
        # Add Nodes
        for i in G.nodes():
            name = num_to_name(i)
            # Default prob 1.0
            prob = 1.0 
            
            p = pos.get(i, (300, 300))
            x = max(50, min(550, p[0]))
            y = max(50, min(550, p[1]))

            new_elements.append({
                'data': {'id': name, 'label': f"{name}\n(P={prob:.2f})", 'name': name, 'probability': prob},
                'position': {'x': x, 'y': y}
            })
            
        # Add Edges
        for u, v in G.edges():
            source = num_to_name(u)
            target = num_to_name(v)
            edge_id = f"{source}->{target}"
            new_elements.append({
                'data': {'source': source, 'target': target, 'id': edge_id}
            })
            
        return new_elements
