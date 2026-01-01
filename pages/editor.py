import dash
import data_handler
import dash_bootstrap_components as dbc
from typing import Any, Hashable, Literal
from dash import html, dcc, Input, Output, State, dash_table, callback, ctx

layout = dbc.Container([
    html.H2("Knowledge Edition", className="mb-4"),

    # add data
    dbc.Card([
        dbc.CardHeader("Data"),
        dbc.CardBody([
            dcc.Input(id="input-data-name", type="text", placeholder="Data name", className="form-input"),
            html.Button("add", id="button-add-data", className="btn-primary"),
            html.Button("remove", id="button-remove-data", className="btn-primary"),
            dcc.Textarea(id="input-data-description", placeholder="Description", style={"width": "100%"}, className="form-input text-area-custom"),
            html.Button("update", id="button-update-data", className="btn-primary"),
            dash_table.DataTable(
                id="table-data",
                style_table={'overflowX': 'auto'},
                columns=[{"name": "Name", "id": "name"}, {"name": "Description", "id": "description"}],
                data=[],
                style_cell={'textAlign': 'left'},
                page_size=10),
            html.Div(id='data-tags', children=[])
            
        ])
    ], className="content-container"),

    # add tag
    dbc.Card([
        dbc.CardHeader("Tags"),
        dbc.CardBody([
            dcc.Input(id="input-tag-name", type="text", placeholder="Tag name", className="form-input"),
            html.Button("add", id="button-add-tag", className="btn-primary"),
            html.Button("remove", id="button-remove-tag", className="btn-primary"),
            dash_table.DataTable(
                id="table-tags",
                style_table={'overflowX': 'auto'},
                columns=[{"name": "Nom", "id": "name"}],
                data=[],
                page_size=10
            )
        ])
    ], className="mb-4"),

    # add relation
    dbc.Card([
        dbc.CardHeader("Relations"),
        dbc.CardBody([
            dcc.Dropdown(id="dropdown-data", placeholder="Select data", className="mb-2"),
            dcc.Dropdown(id="dropdown-tag", placeholder="Select tag", className="mb-2"),
            html.Button("add", id="button-add-relation", className="btn-primary"),
            html.Button("remove", id="button-remove-relation", className="btn-primary"),
            dash_table.DataTable(
                id="table-relations",
                style_table={'overflowX': 'auto'},
                columns=[{"name": "Data", "id": "data_name"}, {"name": "Tag", "id": "tag_name"}],
                data=[],
                page_size=10
            )
        ])
    ]),
], className="card content-container")


@callback(
    Output("table-data", "data"),
    [Input("button-add-data", "n_clicks"),
    Input("button-remove-data", "n_clicks"),
    Input("button-update-data", "n_clicks")],
    [State("input-data-name", "value"),
    State("input-data-description", "value")]
)
def callback_data(add_clicks, rm_clicks, up_clicks, name: str, description: str) -> list[dict[Hashable, Any]]:
    if ctx.triggered_id == "button-add-data" and name and description:
        data_handler.add_data(name, description)
    elif ctx.triggered_id == "button-remove-data" and name:
        data_handler.remove_data(name)
    elif ctx.triggered_id == "button-update-data" and name:
        data_handler.update_data(name, description)
    return data_handler.get_data()

@callback(
    Output("input-data-name", "value"), 
    Output("input-data-description", "value"),
    Output("data-tags", "children"),
    Input("table-data", "active_cell"), 
    State('table-data', 'data')
)
def callback_data_cell(active_cell, table_data) -> tuple[str, str, str]: 
    if active_cell is None:
        return "", "", ""

    name: str = active_cell['row_id']
    description: str = ""
    for row in table_data:
        if row.get('id') == name:
            description = row['description']
    # selected_row = row for row in table_data if row.get('id') == name
    taglist = data_handler.get_tags_from_data(name)
    tags: str = "tags: " + ";".join(taglist)
    return name, description, tags

@callback(
    Output("table-tags", "data"),
    Input("button-add-tag", "n_clicks"),
    Input("button-remove-tag", "n_clicks"),
    State("input-tag-name", "value")
)
def callback_tag(add_clicks, rm_clicks, name: str) -> list[dict[Hashable, Any]]:
    if ctx.triggered_id == "button-add-tag" and name:
        data_handler.add_tag(name)
    elif ctx.triggered_id == "button-remove-tag" and name:
        data_handler.remove_tag(name)
    return data_handler.get_tags()


@callback(
    Output("table-relations", "data"),
    Input("button-add-relation", "n_clicks"),
    Input("button-remove-relation", "n_clicks"),
    State("dropdown-data", "value"),
    State("dropdown-tag", "value")
)
def callback_add_relation(add_clicks, rm_clicks, data_name: str, tag_name: str) -> list[dict[Hashable, Any]]:
    if ctx.triggered_id == "button-add-relation" and data_name and tag_name:
        data_handler.add_relation(data_name, tag_name)
    elif ctx.triggered_id == "button-remoce-relation" and data_name and tag_name: 
        data_handler.remove_relation(data_name, tag_name)
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


