import dash
from dash import html

dash.register_page(__name__, path='/')

layout = html.Div([
    html.H1('This is a tool to list Green IT topics'),
    html.Div('You can add, remove & update entries in the Edition Tab. To select features go to Viewer Tab.'),
])