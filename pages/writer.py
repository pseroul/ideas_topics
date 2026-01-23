from dash import html, Input, Output, dcc, callback
import utils
import json
import os
from data_similarity import DataSimilarity
from typing import List, Dict, Any, Union

# Path to store the cached TOC content
TOC_CACHE_PATH = "data/toc_cache.json"

def save_toc_structure(structure) -> None:
    """
    Save the table of contents structure to a cache file for future use.
    
    This function serializes the hierarchical structure data and stores it in
    a JSON file so that the expensive generation process doesn't need to be
    repeated on every application startup or refresh.
    
    Args:
        structure (list[dict]): The hierarchical structure data to be cached.
            This should be the output from DataSimilarity.generate_toc_structure().
            
    Returns:
        None
    """
    try:
        # Save the raw structure data (which is JSON serializable)
        with open(TOC_CACHE_PATH, 'w') as f:
            json.dump(structure, f)
    except Exception as e:
        print(f"Error saving TOC structure: {e}")

def load_toc_structure():
    """
    Load the table of contents structure from cache file if it exists.
    
    This function attempts to read previously cached structure data from
    the cache file. If the file doesn't exist or is corrupted, it returns None.
    
    Returns:
        list[dict] or None: The cached structure data if available and valid,
            or None if no cache exists or if there was an error loading it.
    """
    try:
        if os.path.exists(TOC_CACHE_PATH):
            with open(TOC_CACHE_PATH, 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading TOC structure: {e}")
    return None

def render_toc_from_structure(structure) -> html.Div:
    """Render the TOC from a structure."""
    
    # Check if structure has the expected format (flat structure from our optimized version)
    if not structure or not isinstance(structure, list):
        # Return empty content if no structure
        return html.Div("No content available", className="card")
    
    # For our simplified structure, we'll create a flat representation
    # --- STEP A : Extract titles for summary ---
    summary_links: List[Union[html.Li, html.Ul]] = []
    
    for i, chap in enumerate(structure):
        chap_id = f"chap-{i}"
        # Add Level 1
        summary_links.append(html.Li(html.A(chap['title'], href=f"#{chap_id}")))
        
        # Add Level 2
        sub_links: List[html.Li] = []
        for j, sec in enumerate(chap.get('children', [])):
            if sec['type'] == 'heading': 
                sec_id = f"sec-{i}-{j}"
                sub_links.append(html.Li(html.A(sec['title'], href=f"#{sec_id}")))
        
        if sub_links:
            summary_links.append(html.Ul(sub_links, style={'listStyleType': 'circle'}))

    # --- STEP B : Body content with link ---   
    def render_body(node: Dict[str, Any], path: str = "0") -> Union[html.Li, html.Div]:
        if node['type'] == 'heading':
            level = node['level']
            
            anchor_id = f"chap-{path}" if level == 1 else f"sec-{path}"
            
            title_style = {
                'fontSize': '1.5em' if level == 1 else '1.2em',
                'fontWeight': 'bold',
                'marginTop': '20px',
                'color': '#2c3e50'
            }
            
            heading_content = html.Div([
                html.Span(node['title'], style={'flex': '1'}),  # Title on left
                html.Span(f"Originality: {node.get('originality', 'N/A')}", 
                            style={'color': '#3498db', 'fontWeight': 'bold'})  # Score on right
            ], style={'display': 'flex', 'justifyContent': 'space-between', 'alignItems': 'center'})
            
            titlesection = None
            if level == 1:
                titlesection = html.H2(heading_content, id=anchor_id, style=title_style)
            else:
                titlesection = html.H3(heading_content, id=anchor_id, style=title_style)
                    
            # Add visual separation for section content with enhanced styling
            section_content = html.Div([
                titlesection,
                html.Ul([render_body(child, f"{path}-{k}") for k, child in enumerate(node['children'])],
                        style={'paddingLeft': '20px', 'borderLeft': '1px solid #ddd', 'marginTop': '15px'})
            ], style={'marginBottom': '30px', 'paddingBottom': '20px', 'borderBottom': '1px solid #eee', 'paddingLeft': '10px'})
            
            return html.Li(section_content)
        else:
            # final idea
            text = utils.unformat_text(node['title'], node["text"])
            full_text = node['title'] + " : " + text
            
            return html.Li([
                html.Span(full_text, style={'flex': '1'}),
                html.Span(f"Originality: {node.get('originality', 'N/A')}", 
                            style={'marginLeft': '20px', 'color': '#3498db', 'fontWeight': 'bold'})
            ], style={'display': 'flex', 'justifyContent': 'space-between', 'alignItems': 'center', 'color': '#7f8c8d', 'fontSize': '0.9em'})
        

    # --- STEP C : Final assembly ---
    final_render = html.Div([
        # Content
        html.Div([
            html.H2("Contents", style={'borderBottom': '2px solid #3498db', 'paddingBottom': '10px', 'marginBottom': '20px'}),
            html.Ul(summary_links, style={'lineHeight': '1.8em'})
        ], style={'backgroundColor': '#f8f9fa', 'padding': '20px', 'borderRadius': '8px', 'marginBottom': '30px', 'boxShadow': '0 2px 4px rgba(0,0,0,0.05)'}),
        
        # Body with improved section separation
        html.Div([
            render_body(item, str(i)) for i, item in enumerate(structure)
        ], style={'marginBottom': '40px'})
    ], style={'padding': '20px'})
    return final_render

layout = html.Div([
    html.H1("White Paper"),
    
    html.Div([
        html.Button("Refresh contents", id="btn-toc", n_clicks=0, className="btn-secondary"),
        dcc.Loading(
            id="loading-toc",
            type="circle",
            children=html.Div(id="toc-display", className="card")
        )
    ], className="card")
])

@callback(
    Output("toc-display", "children"),
    Input("btn-toc", "n_clicks")
)
def update_toc(n_clicks: int) -> Union[html.Div, Any]:
    """
    Update the table of contents and content display.
    
    This callback generates a hierarchical table of contents and content
    structure from the embedded data using the Embedder's generate_toc_structure method.
    
    When the page loads, it will attempt to load cached content. When the refresh
    button is clicked, it will regenerate the content and save it to cache.
    
    Args:
        n_clicks (int): Number of times the refresh button was clicked
        
    Returns:
        html.Div: The rendered table of contents and content structure
    """
    
    # On first load (n_clicks = 0), try to load cached structure
    # On subsequent clicks, always regenerate and save new structure
    if n_clicks == 0:
        print("load_toc_structure")
        cached_structure = load_toc_structure()
        if cached_structure is not None:
            # Return cached content if available on first load
            # Hide loading indicator when done
            print("reuse cache value")
            return render_toc_from_structure(cached_structure)
    
    # Generate new structure (either on first load with no cache, or on button click)
    toc_builder = DataSimilarity()
    print("generate_toc_structure")
    structure = toc_builder.generate_toc_structure()

    # Save the generated structure for future use
    save_toc_structure(structure)
    
    # Render and return the content
    return render_toc_from_structure(structure)
