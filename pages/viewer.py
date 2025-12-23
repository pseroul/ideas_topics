import dash
import data_handler
import dash_bootstrap_components as dbc
from typing import Any, Hashable
from dash import dcc, html, Input, Output, State, dash_table, callback


dash.register_page(__name__)

layout = dbc.Container([
    html.H2("Knowledge Parser", className="mb-4"),

    dbc.Card([
        dbc.CardHeader("Data"),
        dbc.CardBody([
            dcc.Input(id="viewer-input-tag-name", type="text", placeholder="Tag name search", className="mb-2"),
            dbc.Button("Search", id="viewer-button-search-tag"),
            dash_table.DataTable(
                id="viewer-table-data",
                columns=[{"name": "Nom", "id": "name"}, {"name": "Description", "id": "description"}],
                data=[],
                page_size=10,
            )
        ])
    ], className="mb-4")
])

# Callbacks
@callback(
    Output("viewer-table-data", "data"),
    Input("viewer-button-search-tag", "n_clicks"),
    State("viewer-input-tag-name", "value"),
)
def callback_add_data(n_clicks, tags: str) -> list[dict[Hashable, Any]]:
    return data_handler.get_data_from_tags(tags)