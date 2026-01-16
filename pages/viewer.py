from plotly.graph_objs._figure import Figure
import data_handler
from typing import Any
from dash import dcc, html, Input, Output, State, dash_table, callback
import dash_cytoscape as cyto
from data_visualizer import get_network_recursive, umap_all_data
import plotly.express as px
import config 

def get_all_inputs(): 
    data_name = data_handler.get_data()
    tag_name = data_handler.get_tags()

    inputs = [{'label': data['name'], 'value': data['name']} for data in data_name]
    inputs += [{'label': tag['name'], 'value': tag['name']} for tag in tag_name]
    return inputs


# fill combobox
inputs = get_all_inputs()

layout = html.Div([
    html.H1("Idea explorer"),
    html.Div([
        dcc.Dropdown(id='input-name', placeholder='Idea / Notes...', options=inputs),
        html.Button('See connections', id='btn-submit', n_clicks=0, className="btn-primary"),
    ]),
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
    Output('node-info', 'children'),
    Output('table-viz-data', 'data'),
    Input('btn-submit', 'n_clicks'),
    State('input-name', 'value')
)
def update_connection_graph(n_clicks: int, input_value: str):
    if n_clicks > 0 and input_value:
        description = data_handler.get_description(input_value)
        print(description)
        div = html.Div([html.H3(f"Nom : {input_value}"),html.P(f"Description : {description}")])
        k_nearest = data_handler.get_similar_data(input_value)
        return div, k_nearest
    return "Click on a node to see its description", []
