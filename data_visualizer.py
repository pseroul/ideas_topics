
import sqlite3
from typing import Any
import pandas as pd
from data_similarity import Embeddings
from config import NAME_DB


def get_network_recursive(start_node: str, max_depth: int=2) -> list[dict[str, Any]]:
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
        # query = "SELECT data_name, tag_name FROM relation WHERE data_name = ? OR tag_name = ?"
        # df_links = pd.read_sql(query, conn, params=(current_node, current_node))
        query = "SELECT description FROM data WHERE name = (?)"
        description = pd.read_sql(query, conn, params=[current_node])
        embedding = Embeddings()
        similar_data = embedding.get_similar_data(current_node, description.iloc[0], n_results=int(8/(depth+1)))
        
        for sd in similar_data:
            neighbor = sd['name']
            if neighbor == current_node:
                continue
            
            # Ajout du lien pour Cytoscape
            edges.append({
                'data': {'source': current_node, 'target': neighbor}
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