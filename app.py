import os
import dash
from data_handler import init_database
from dash import Dash, dcc, html
import dash_bootstrap_components as dbc

init_database()

app = Dash(__name__, use_pages=True, external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = dbc.Container([
    dbc.Row([
        dbc.Col(html.H1("Knowledge on Sustainable & Green IT", className="text-center mb-4")),
    ]),
    dbc.Row([
        dbc.Col(dcc.Link(f"{page['name']}", href=page["relative_path"], className="btn btn-primary mb-2"),
                width="auto")
        for page in dash.page_registry.values()
    ]),
    dash.page_container
], fluid=True)

if __name__ == "__main__":
    dir_path = os.path.dirname(os.path.realpath(__file__))
    app.run(debug=True)
