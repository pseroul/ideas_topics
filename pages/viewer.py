import dash
import data_handler
import dash_bootstrap_components as dbc
from typing import Any, Hashable
from dash import dcc, html, Input, Output, State, dash_table, callback
import dash_cytoscape as cyto
from data_visualizer import get_network_recursive

def get_all_inputs(): 
    data_name = data_handler.get_data()
    tag_name = data_handler.get_tags()

    inputs = [{'label': data['name'], 'value': data['name']} for data in data_name]
    inputs += [{'label': tag['name'], 'value': tag['name']} for tag in tag_name]
    return inputs

inputs = get_all_inputs()

layout = html.Div([
    html.H1("Idea explorer"),
    html.Div([
        dcc.Dropdown(id='input-name', placeholder='Idea / Notes...', options=inputs),
        html.Button('Generate', id='btn-submit', n_clicks=0, className="btn-primary"),
    ]),
    
    cyto.Cytoscape(
        id='cytoscape-graph',
        layout={'name': 'cose'}, 
        style={'width': '100%', 'height': '600px'},
        elements=[],
        stylesheet=[
            {
                'selector': 'node',
                'style': {
                    'label': 'data(label)',
                    'background-color': '#0074D9',
                    'color': 'black'
                }
            },
            {
                'selector': 'edge',
                'style': {'line-color': '#999'}
            }
        ]
    ),
    html.Div(id='node-info')
], className="content-container")

@callback(
    Output('cytoscape-graph', 'elements'),
    Input('btn-submit', 'n_clicks'),
    State('input-name', 'value')
)
def update_graph(n_clicks, input_value):
    if n_clicks > 0 and input_value:
        return get_network_recursive(input_value)
    return []

@callback(
    Output('node-info', 'children'),
    Input('cytoscape-graph', 'tapNodeData')
)
def display_node_data(data: dict[str]) -> html.Div | str:
    if data:
        return html.Div([
            html.H3(f"Nom : {data['label']}"),
            html.P(f"Description : {data['desc']}")
        ])
    return "Cliquez sur un nœud pour voir sa description."
