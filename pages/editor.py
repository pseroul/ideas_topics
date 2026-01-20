import data_handler
import dash_bootstrap_components as dbc
from typing import Any, Hashable
from dash import html, dcc, Input, Output, State, dash_table, callback, ctx

layout = dbc.Container([
    html.H2("Knowledge Edition", className="mb-4"),

    # add data
    dbc.Card([
        dbc.CardHeader("Data"),
        dbc.CardBody([
            dcc.Input(id="input-data-name", type="text", placeholder="Data name", className="form-input"),
            dcc.Textarea(id="input-data-description", placeholder="Description", style={"width": "100%"}, className="form-input text-area-custom"),
            html.Div(id='data-tags', children=[]),
            html.Div([html.Button("add", id="button-add-data", className="btn-primary"),
                     html.Button("remove", id="button-remove-data", className="btn-danger")], className="button-row"),
            html.Button("update", id="button-update-data", className="btn-primary"),
            dcc.Dropdown(id="dropdown-tag", placeholder="Select tag", className="mb-2"),
            html.Div([html.Button("add tag", id="button-add-relation", className="btn-primary"),
            html.Button("remove tag", id="button-remove-relation", className="btn-danger")], className="button-row"),
            dash_table.DataTable(
                id="table-data",
                style_table={'overflowX': 'auto'},
                columns=[{"name": "Name", "id": "name"}, {"name": "Description", "id": "description"}],
                data=[],
                style_cell={'textAlign': 'left'},
                page_size=10)
        ])
    ], className="content-container"),

    # add tag
    dbc.Card([
        dbc.CardHeader("Tags"),
        dbc.CardBody([
            dcc.Input(id="input-tag-name", type="text", placeholder="Tag name", className="form-input"),
            html.Div([html.Button("add", id="button-add-tag", className="btn-primary"),
                      html.Button("remove", id="button-remove-tag", className="btn-danger")], className="button-row"),
            dash_table.DataTable(
                id="table-tags",
                style_table={'overflowX': 'auto'},
                columns=[{"name": "Nom", "id": "name"}],
                data=[],
                page_size=10
            )
        ])
    ], className="mb-4")

], className="card content-container")


@callback(
    Output("table-data", "data"),
    [Input("button-add-data", "n_clicks"),
    Input("button-remove-data", "n_clicks"),
    Input("button-update-data", "n_clicks"), 
    Input("input-data-name", "value")],
    State("input-data-description", "value")
)
def callback_data(add_clicks, rm_clicks, up_clicks, name: str, description: str) -> list[dict[Hashable, Any]]:
    """
    Handle data addition, removal, and update operations.
    
    This callback manages all data-related operations including:
    - Adding new data items
    - Removing existing data items
    - Updating existing data items
    
    Args:
        add_clicks (int): Number of times the add button was clicked
        rm_clicks (int): Number of times the remove button was clicked
        up_clicks (int): Number of times the update button was clicked
        name (str): The name of the data item
        description (str): The description of the data item
        
    Returns:
        list[dict[Hashable, Any]]: Updated list of data items for the table
    """
    if ctx.triggered_id == "button-add-data" and name and description:
        data_handler.add_data(name.strip(), description)
    elif ctx.triggered_id == "button-remove-data" and name:
        data_handler.remove_data(name)
    elif ctx.triggered_id == "button-update-data" and name:
        data_handler.update_data(name, description)    
    return data_handler.get_selected_data(name)

@callback(
    Output("input-data-name", "value"), 
    Output("input-data-description", "value"),
    Output("data-tags", "children"),
    Input("table-data", "active_cell"), 
    State('table-data', 'data')
)
def callback_data_cell(active_cell, table_data) -> tuple[str, str, str]: 
    """
    Populate form fields when a data cell is selected.
    
    This callback fills the input fields with the selected data item's information
    and retrieves associated tags for display.
    
    Args:
        active_cell (dict): The currently active cell in the table
        table_data (list[dict]): The complete data table contents
        
    Returns:
        tuple[str, str, str]: Tuple containing (name, description, tags) for the selected item
    """
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
    Output("data-tags", "children", allow_duplicate=True),
    Input("button-add-relation", "n_clicks"),
    Input("button-remove-relation", "n_clicks"),
    State("input-data-name", "value"),
    State("dropdown-tag", "value"),
    prevent_initial_call=True
)
def callback_relation(add_clicks, rm_clicks, data_name: str, tag_name: str) -> list[dict[Hashable, Any]]:
    """
    Manage relationships between data items and tags.
    
    This callback handles adding and removing relationships between data items
    and tags in the database.
    
    Args:
        add_clicks (int): Number of times the add relation button was clicked
        rm_clicks (int): Number of times the remove relation button was clicked
        data_name (str): The name of the data item
        tag_name (str): The name of the tag
        
    Returns:
        list[dict[Hashable, Any]]: Updated tags display for the data item
    """
    if ctx.triggered_id == "button-add-relation" and data_name and tag_name:
        data_handler.add_relation(data_name, tag_name)
    elif ctx.triggered_id == "button-remoce-relation" and data_name and tag_name: 
        data_handler.remove_relation(data_name, tag_name)
    taglist = data_handler.get_tags_from_data(data_name)
    tags: str = "tags: " + ";".join(taglist)
    return tags

@callback(
    Output("table-tags", "data"),
    Input("button-add-tag", "n_clicks"),
    Input("button-remove-tag", "n_clicks"),
    State("input-tag-name", "value")
)
def callback_tag(add_clicks, rm_clicks, name: str) -> list[dict[Hashable, Any]]:
    """
    Handle tag addition and removal operations.
    
    This callback manages all tag-related operations including:
    - Adding new tags
    - Removing existing tags
    
    Args:
        add_clicks (int): Number of times the add tag button was clicked
        rm_clicks (int): Number of times the remove tag button was clicked
        name (str): The name of the tag to add/remove
        
    Returns:
        list[dict[Hashable, Any]]: Updated list of tags for the table
    """
    if ctx.triggered_id == "button-add-tag" and name:
        data_handler.add_tag(name.strip())
    elif ctx.triggered_id == "button-remove-tag" and name:
        data_handler.remove_tag(name)
    return data_handler.get_tags()

@callback(
    Output("dropdown-tag", "options"),
    Input("table-tags", "data")
)
def update_dropdown_tags(tags: list[dict[str, str]]) -> list[dict[str, str]]:
    """
    Update the dropdown options with available tags.
    
    This callback dynamically updates the tag dropdown menu with the current
    list of available tags from the database.
    
    Args:
        tags (list[dict[str, str]]): List of available tags
        
    Returns:
        list[dict[str, str]]: Options for the dropdown menu
    """
    return [{"label": t["name"], "value": t["name"]} for t in tags]
