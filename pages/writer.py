from dash import html, Input, Output, callback
from data_similarity import Embeddings

layout = html.Div([
    html.H1("White Paper"),
    
    html.Div([
        html.Button("Refresh contents", id="btn-toc", n_clicks=0, className="btn-secondary"),
        html.Div(id="toc-display", className="card")
    ], className="card")
])


@callback(
    Output("toc-display", "children"),
    Input("btn-toc", "n_clicks"),
    prevent_initial_call=True
)
def update_toc(n) -> html.Ul:
    embeddings = Embeddings()
    structure = embeddings.generate_toc_structure()

    def render_node(node):
    # Style différent selon le niveau
        if node['type'] in ['chapter', 'section']:
            is_chapter = node['level'] == 1
            title_style = {
                'fontSize': '1.3em' if is_chapter else '1.1em',
                'fontWeight': 'bold',
                'color': '#2c3e50' if is_chapter else '#34495e',
                'marginTop': '15px' if is_chapter else '5px',
                'listStyleType': 'none'
            }
            
            return html.Li([
                html.Div(f"{node['title']}", style=title_style),
                html.Ul([render_node(child) for child in node['children']], 
                        style={'paddingLeft': '20px', 'borderLeft': '1px solid #ddd'})
            ])
        else:
            # C'est une idée finale (feuille de l'arbre)
            text = embeddings._unformat_text(node['title'], node["text"])
            text = node['title'] + " : " + text
            return html.Li(text , style={'color': '#7f8c8d', 'fontSize': '0.9em'})

    return html.Ul([render_node(item) for item in structure])