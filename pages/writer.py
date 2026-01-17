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
def update_toc(n) -> html.Div:
    embeddings = Embeddings()
    structure = embeddings.generate_toc_structure()

    # --- STEP A : Extract titles for summary ---
    summary_links = []
    
    for i, chap in enumerate(structure):
        chap_id = f"chap-{i}"
        # Add Level 1
        summary_links.append(html.Li(html.A(chap['title'], href=f"#{chap_id}")))
        
        # Add Level 2
        sub_links = []
        for j, sec in enumerate(chap.get('children', [])):
            if sec['type'] == 'heading': 
                sec_id = f"sec-{i}-{j}"
                sub_links.append(html.Li(html.A(sec['title'], href=f"#{sec_id}")))
        
        if sub_links:
            summary_links.append(html.Ul(sub_links, style={'listStyleType': 'circle'}))

    # --- STEP B : Body content with link ---
    def render_body(node, path="0") -> html.Div | html.Li:
        node_id = f"anchor-{path}"
        
        if node['type'] == 'heading':
            level = node['level']
            
            anchor_id = f"chap-{path}" if level == 1 else f"sec-{path}"
            
            title_style = {
                'fontSize': '1.5em' if level == 1 else '1.2em',
                'fontWeight': 'bold',
                'marginTop': '20px',
                'color': '#2c3e50'
            }
            
            titlesection = None
            if level == 1:
                titlesection = html.H2(node['title'], id=anchor_id, style=title_style)
            else:
                titlesection = html.H3(node['title'], id=anchor_id, style=title_style)
            return html.Li([titlesection,
                            html.Ul([render_body(child, f"{path}-{k}") for k, child in enumerate(node['children'])],
                                    style={'paddingLeft': '20px', 'borderLeft': '1px solid #ddd'})])
        else:
            # final idea
            text = embeddings._unformat_text(node['title'], node["text"])
            text = node['title'] + " : " + text
            return html.Li(text , style={'color': '#7f8c8d', 'fontSize': '0.9em'})
        

    # --- STEP C : Final assembly ---
    final_render = html.Div([
        # Content
        html.Div([
            html.H2("Contents", style={'borderBottom': '2px solid #3498db', 'paddingBottom': '10px'}),
            html.Ul(summary_links, style={'lineHeight': '1.8em'})
        ], style={'backgroundColor': '#f8f9fa', 'padding': '20px', 'borderRadius': '8px', 'marginBottom': '40px'}),
        
        html.Hr(),
        
        # Body
        html.Div([
            render_body(item, str(i)) for i, item in enumerate(structure)
        ])
    ])
    return final_render