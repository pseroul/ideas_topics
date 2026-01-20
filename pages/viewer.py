import data_handler
from dash import dcc, html, Input, Output, State, dash_table, callback

def get_all_inputs(): 
    """
    Get all available data and tag inputs for the dropdown.
    
    This function retrieves all data items and tags from the data handler
    to populate the dropdown menu with selectable options.
    
    Returns:
        list[dict[str, str]]: List of dictionaries containing label and value pairs
    """
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
    """
    Update the connection graph and related data table.
    
    This callback handles the submission of a selected item to display
    its connections and related data in the visualization interface.
    
    Args:
        n_clicks (int): Number of times the submit button was clicked
        input_value (str): The selected value from the dropdown
        
    Returns:
        tuple[html.Div, list[dict[str, str]]]: Tuple containing the node info display
            and the related data table contents
    """
    if n_clicks > 0 and input_value:
        description = data_handler.get_description(input_value)
        print(description)
        div = html.Div([html.H3(f"Nom : {input_value}"),html.P(f"Description : {description}")])
        k_nearest = data_handler.get_similar_data(input_value)
        return div, k_nearest
    return "Click on a node to see its description", []
