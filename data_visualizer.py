
import sqlite3
from typing import Any, Hashable
import pandas as pd
import data_handler
from config import NAME_DB


def get_network_recursive(start_node: str, max_depth=3):# -> list[Any]:
    """
    Recursive parsing of data
    """
    conn = sqlite3.connect(NAME_DB)
    nodes = set()
    edges = []
    visited = set()

    def fetch_neighbors(current_node: str, depth: int) -> None:
        if depth > max_depth or current_node in visited:
            return
        visited.add(current_node)
        
        # Looking for links between data and tags
        query = "SELECT data_name, tag_name FROM relation WHERE data_name = ? OR tag_name = ?"
        df_links = pd.read_sql(query, conn, params=(current_node, current_node))
        
        for _, row in df_links.iterrows():
            neighbor = row['tag_name'] if row['data_name'] == current_node else row['data_name']
            
            # Ajout du lien pour Cytoscape
            edges.append({
                'data': {'source': row['data_name'], 'target': row['tag_name']}
            })
            
            nodes.add(current_node)
            nodes.add(neighbor)
            
            # Recursive call
            fetch_neighbors(neighbor, depth + 1)

    fetch_neighbors(start_node, 0)
    
    # Description retrieval
    node_elements = []
    if nodes:
        placeholders = ', '.join(['?'] * len(nodes))
        query_desc = f"SELECT name, description FROM data WHERE name IN ({placeholders})"
        df_desc = pd.read_sql(query_desc, conn, params=list(nodes))
        
        for _, row in df_desc.iterrows():
            node_elements.append({
                'data': {'id': row['name'], 'label': row['name'], 'desc': row['description']}
            })
            nodes.discard(row['name'])

        for tag in nodes:
            node_elements.append({
                'data': {'id': tag, 'label': tag, 'desc': 'tag'}
            })
            
    conn.close()
    return node_elements + edges