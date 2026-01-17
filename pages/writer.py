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

    # --- ÉTAPE A : Extraire les titres Niv 1 et 2 pour le sommaire ---
    summary_links = []
    
    for i, chap in enumerate(structure):
        chap_id = f"chap-{i}"
        # Ajout Niveau 1
        summary_links.append(html.Li(html.A(chap['title'], href=f"#{chap_id}")))
        
        # Ajout Niveau 2 (sous-sections)
        sub_links = []
        for j, sec in enumerate(chap.get('children', [])):
            if sec['type'] == 'heading': # On ne liste pas les idées brutes ici
                sec_id = f"sec-{i}-{j}"
                sub_links.append(html.Li(html.A(sec['title'], href=f"#{sec_id}")))
        
        if sub_links:
            summary_links.append(html.Ul(sub_links, style={'listStyleType': 'circle'}))

    # --- ÉTAPE B : Fonctions de rendu du corps avec ID d'ancrage ---
    def render_body(node, path="0") -> html.Div | html.Li:
        node_id = f"anchor-{path}"
        
        if node['type'] == 'heading':
            level = node['level']
            # On définit l'ID pour l'hyperlien (compatible avec le sommaire)
            # path est de la forme "i" pour chapitre, "i-j" pour section
            anchor_id = f"chap-{path}" if level == 1 else f"sec-{path}"
            
            title_style = {
                'fontSize': '1.5em' if level == 1 else '1.2em',
                'fontWeight': 'bold',
                'marginTop': '20px',
                'color': '#2c3e50'
            }
            
            return html.Div([
                html.H2(node['title'], id=anchor_id, style=title_style) if level == 1 
                else html.H3(node['title'], id=anchor_id, style=title_style),
                html.Ul([
                    render_body(child, f"{path}-{k}") 
                    for k, child in enumerate(node['children'])
                ], style={'paddingLeft': '20px'})
            ])
        else:
            text = node['title']
            if 'text' in node:
                text = text + " : " + embeddings._unformat_text(node['title'], node["text"])
            return html.Li(text, style={'color': '#444', 'margin': '5px 0'})

    # --- ÉTAPE C : Assemblage Final ---
    final_render = html.Div([
        # Bloc Sommaire
        html.Div([
            html.H2("Sommaire Rapide", style={'borderBottom': '2px solid #3498db', 'paddingBottom': '10px'}),
            html.Ul(summary_links, style={'lineHeight': '1.8em'})
        ], style={'backgroundColor': '#f8f9fa', 'padding': '20px', 'borderRadius': '8px', 'marginBottom': '40px'}),
        
        html.Hr(),
        
        # Corps du texte
        html.Div([
            render_body(item, str(i)) for i, item in enumerate(structure)
        ])
    ])
    return final_render