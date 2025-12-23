import dash
import data_handler
import dash_bootstrap_components as dbc
from typing import Any, Hashable
from dash import html, dcc, Input, Output, State, dash_table, callback


dash.register_page(__name__, name="Edition")

layout = dbc.Container([
    html.H2("Knowledge Edition", className="mb-4"),

    # add data
    dbc.Card([
        dbc.CardHeader("Data"),
        dbc.CardBody([
            dcc.Input(id="input-data-name", type="text", placeholder="Data name", className="mb-2"),
            dcc.Input(id="input-data-description", type="text", placeholder="Description", className="mb-2"),
            dbc.Button("add", id="button-add-data", color="primary"),
            dash_table.DataTable(
                id="table-data",
                columns=[{"name": "Nom", "id": "name"}, {"name": "Description", "id": "description"}],
                data=[],
                page_size=10,
            )
        ])
    ], className="mb-4"),

    # add tag
    dbc.Card([
        dbc.CardHeader("Add tag"),
        dbc.CardBody([
            dcc.Input(id="input-tag-name", type="text", placeholder="Tag name", className="mb-2"),
            dbc.Button("add", id="button-add-tag", color="primary"),
            dash_table.DataTable(
                id="table-tags",
                columns=[{"name": "Nom", "id": "name"}],
                data=[],
                page_size=10,
            )
        ])
    ], className="mb-4"),

    # add relation
    dbc.Card([
        dbc.CardHeader("add relation"),
        dbc.CardBody([
            dcc.Dropdown(id="dropdown-data", placeholder="Select data", className="mb-2"),
            dcc.Dropdown(id="dropdown-tag", placeholder="Select tag", className="mb-2"),
            dbc.Button("add", id="button-add-relation", color="primary"),
            dash_table.DataTable(
                id="table-relations",
                columns=[{"name": "Data", "id": "data_name"}, {"name": "Tag", "id": "tag_name"}],
                data=[],
                page_size=10,
            )
        ])
    ]),
])


# Callbacks
@callback(
    Output("table-data", "data"),
    Input("button-add-data", "n_clicks"),
    State("input-data-name", "value"),
    State("input-data-description", "value"),
)
def callback_add_data(n_clicks, name: str, description: str) -> list[dict[Hashable, Any]]:
    if n_clicks and name and description:
        data_handler.add_data(name, description)
    return data_handler.get_data()

@callback(
    Output("table-tags", "data"),
    Input("button-add-tag", "n_clicks"),
    State("input-tag-name", "value"),
)
def callback_add_tag(n_clicks, name: str) -> list[dict[Hashable, Any]]:
    if n_clicks and name:
        data_handler.add_tag(name)
    return data_handler.get_tags()

@callback(
    Output("table-relations", "data"),
    Input("button-add-relation", "n_clicks"),
    State("dropdown-data", "value"),
    State("dropdown-tag", "value"),
)
def callback_add_relation(n_clicks, data_name: str, tag_name: str) -> list[dict[Hashable, Any]]:
    if n_clicks and data_name and tag_name:
        data_handler.add_relation(data_name, tag_name)
    return data_handler.get_relations()

@callback(
    Output("dropdown-data", "options"),
    Input("table-data", "data")
)
def update_dropdown_datas(data):
    return [{"label": d["name"], "value": d["name"]} for d in data]

@callback(
    Output("dropdown-tag", "options"),
    Input("table-tags", "data")
)
def update_dropdown_tags(data):
    return [{"label": t["name"], "value": t["name"]} for t in data]


