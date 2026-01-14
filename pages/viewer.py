import dash
import data_handler
from typing import Any, Hashable
from dash import dcc, html, Input, Output, State, dash_table, callback
import dash_cytoscape as cyto
from data_visualizer import get_network_recursive, umap_all_data
import plotly.express as px

def get_all_inputs(): 
    data_name = data_handler.get_data()
    tag_name = data_handler.get_tags()

    inputs = [{'label': data['name'], 'value': data['name']} for data in data_name]
    inputs += [{'label': tag['name'], 'value': tag['name']} for tag in tag_name]
    return inputs


# fill combobox
inputs = get_all_inputs()

# Fill scatter plot containing all data
data_projection = umap_all_data()
fig = px.scatter(data_projection, x='x', y='y', hover_name='text', template="plotly_white")
fig.update_layout(
    margin=dict(l=10, r=10, t=40, b=10),
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=-0.3, 
        xanchor="center",
        x=0.5
    ),
    
    font=dict(size=14),
    
    hovermode="closest",
    hoverlabel=dict(
        bgcolor="white",
        font_size=16,
        font_family="Rockwell"
    )
)

fig.update_traces(marker=dict(size=12, line=dict(width=1, color='DarkSlateGrey')))

default_cytoscape_stylesheet = [
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

layout = html.Div([
    html.H1("Idea explorer"),
    html.Div([
        dcc.Graph(
            id='embedding-graph',
            figure=fig,
            config={
            'displayModeBar': False, # Hide the toolbar to save space
            'scrollZoom': False
            },
            style={'height': '70vh', 'width': '100%'} # Use viewport height
        )
    ]),
    html.Div([
        dcc.Dropdown(id='input-name', placeholder='Idea / Notes...', options=inputs),
        html.Button('Generate', id='btn-submit', n_clicks=0, className="btn-primary"),
    ]),
    
    cyto.Cytoscape(
        id='cytoscape-graph',
        layout={'name': 'cose'}, 
        style={'width': '100%', 'height': '600px'},
        elements=[],
        stylesheet=default_cytoscape_stylesheet
    ),
    html.Div(id='node-info'),
    dash_table.DataTable(
        id="table-viz-data",
        style_table={'overflowX': 'auto'},
        columns=[{"name": "Name", "id": "name"}, {"name": "Description", "id": "description"}],
        data=[],
        style_cell={'textAlign': 'left'},
        page_size=10)
], className="content-container")

@callback(
    Output('cytoscape-graph', 'elements'),
    Input('btn-submit', 'n_clicks'),
    State('input-name', 'value')
)
def update_graph(n_clicks, input_value: str):
    if n_clicks > 0 and input_value:
        graph = get_network_recursive(input_value)
        return graph
    return []

@callback(
    Output('node-info', 'children'),
    Output('cytoscape-graph', 'stylesheet'),
    Output('table-viz-data', 'data'),
    Input('cytoscape-graph', 'tapNodeData'),
    State('cytoscape-graph', 'elements')
)
def display_node_data(data: dict[str, str], elements: dict[str, Any]) -> tuple[html.Div, dict[str, Any], list[dict[str, Any]]]:
    if data:
        div = html.Div([html.H3(f"Nom : {data['label']}"),html.P(f"Description : {data['desc']}")])
        selected_node_stylesheet = {
            'selector': f'node[id = "{data["id"]}"]',
            'style': {'background-color': '#FF851B', 'line-color': '#FF4136'}
        }
        selected_edge_stylesheet = []
        for element in elements:
            if 'source' in element['data'] and element['data']['source'] == data["id"]:
                selected_edge_stylesheet.append({
                    'selector': f'edge[id = "{element["data"]["id"]}"]',
                    'style': {'line-color': '#FF851B', 'width': 4}})

        stylesheet = default_cytoscape_stylesheet + [selected_node_stylesheet] + selected_edge_stylesheet
        k_nearest = data_handler.get_similar_data(data['label'])

        return div, stylesheet, k_nearest
        
    return "Click on a node to see its description and its neighboors", default_cytoscape_stylesheet, []
