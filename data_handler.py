import sqlite3
from typing import Any, Hashable
import pandas as pd
from chroma_client import ChromaClient
from config import NAME_DB
import argparse
from concurrent.futures import ThreadPoolExecutor


def init_database() -> None:
    """
    Initialize the SQLite database with required tables.
    
    Creates three tables if they don't exist:
    - tags: stores tag information
    - data: stores data items with descriptions
    - relation: manages many-to-many relationships between data and tags
    
    Returns:
        None
    """
    conn = sqlite3.connect(NAME_DB)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tags (name TEXT PRIMARY KEY);
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS data (name TEXT PRIMARY KEY, description TEXT, tags TEXT);
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS relation (
        data_name TEXT,
        tag_name TEXT,
        PRIMARY KEY (data_name, tag_name),
        FOREIGN KEY (data_name) REFERENCES data(name),
        FOREIGN KEY (tag_name) REFERENCES tags(name)
    );
    """)

    conn.commit()
    conn.close()

# GET DATA OR TAGS
def get_data_from_tags(tags: str, limit: int = 500) -> list[dict[Hashable, str]]:
    """
    Retrieve data items associated with specific tags.
    
    Fetches data items that are linked to the specified tags from the database.
    
    Args:
        tags (str): Semicolon-separated string of tag names
        limit (int): Maximum number of results to return to limit memory usage
        
    Returns:
        list[dict[Hashable, str]]: List of dictionaries containing data items
    """
    if not tags:
        return get_data(limit)
    else:
        tags_list = tags.split(";")
        placeholders = ", ".join(["?"] * len(tags_list))
        conn = sqlite3.connect(NAME_DB)
        query = f"""
        SELECT DISTINCT d.name, d.description
        FROM data d
        JOIN relation r ON d.name = r.data_name
        JOIN tags t ON r.tag_name = t.name
        WHERE t.name IN ({placeholders})
        LIMIT {limit};
        """
        df = pd.read_sql_query(query, conn, params=tags_list)
        conn.close()
    return df.to_dict("records")

def get_data(limit: int = 500) -> list[dict[Hashable, Any]]:
    """
    Retrieve all data items from the database with limit to prevent memory issues.
    
    Gets all records from the data table in the SQLite database.
    
    Args:
        limit (int): Maximum number of records to return
        
    Returns:
        list[dict[Hashable, Any]]: List of dictionaries containing all data items
    """
    conn = sqlite3.connect(NAME_DB)
    query = f"SELECT * FROM data LIMIT {limit}"
    df = pd.read_sql_query(query, conn)
    df['id'] = df['name']
    conn.close()
    return df.to_dict("records")

def get_selected_data(subname: str) -> list[dict[Hashable, Any]]:
    """
    Retrieve data items matching a partial name search.
    
    Searches for data items whose names contain the specified substring.
    
    Args:
        subname (str): Substring to search for in data names
        
    Returns:
        list[dict[Hashable, Any]]: List of dictionaries containing matching data items
    """
    subname = "%" + subname + "%"
    conn = sqlite3.connect(NAME_DB)
    df = pd.read_sql_query("SELECT * FROM data WHERE name LIKE (?)", conn, params=[subname])
    df['id'] = df['name']
    conn.close()
    return df.to_dict("records")

def get_description(data_name: str) -> str:
    """
    Retrieve the description of a specific data item.
    
    Gets the description for a data item with the specified name.
    
    Args:
        data_name (str): Name of the data item to retrieve description for
        
    Returns:
        str: Description of the data item
    """
    conn = sqlite3.connect(NAME_DB)
    df = pd.read_sql_query("SELECT description FROM data WHERE name=(?)", conn, params=[data_name])
    conn.close()
    return df['description'].iloc[0]

def get_tags() -> list[dict[Hashable, Any]]:
    """
    Retrieve all tags from the database.
    
    Gets all records from the tags table in the SQLite database.
    
    Returns:
        list[dict[Hashable, Any]]: List of dictionaries containing all tags
    """
    conn = sqlite3.connect(NAME_DB)
    df = pd.read_sql_query("SELECT * FROM tags", conn)
    conn.close()
    return df.to_dict("records")

def get_tags_from_data(data: str):
    """
    Retrieve tags associated with a specific data item.
    
    Gets all tags that are linked to the specified data item.
    
    Args:
        data (str): Name of the data item to retrieve tags for
        
    Returns:
        list[str]: List of tag names associated with the data item
    """
    if not data:
        return get_tags()
    else:
        conn = sqlite3.connect(NAME_DB)
        query = "SELECT tag_name FROM relation WHERE data_name = (?)"
        df = pd.read_sql_query(query, conn, params=[data])
        conn.close()
    return df['tag_name'].to_list()

def get_similar_data(data: str) -> None:
    """
    Find similar data items based on semantic similarity.
    
    Uses the ChromaClient to find data items similar to the specified data item.
    
    Args:
        data (str): Name of the data item to find similar items for
        
    Returns:
        None: Results are returned through the ChromaClient's get_similar_data method
    """
    conn = sqlite3.connect(NAME_DB)
    query = "SELECT name, description FROM data WHERE name = (?)"
    df = pd.read_sql_query(query, conn, params=[data])
    chroma = ChromaClient()
    results = chroma.get_similar_data(df['name'], df['description'])
    conn.close()
    return results

# ADD FUNCTIONS
def add_data(name: str, description: str) -> None:
    """
    Add a new data item to the database.
    
    Inserts a new record into the data table and adds the corresponding
    embedding to the ChromaClient.
    
    Args:
        name (str): Name of the data item to add
        description (str): Description of the data item to add
        
    Returns:
        None
    """
    conn = sqlite3.connect(NAME_DB)
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO data (name, description) VALUES (?, ?)",
            (name, description)
        )
        conn.commit()
        
        # Run embedding insertion asynchronously using thread pool
        with ThreadPoolExecutor() as executor:
            future = executor.submit(lambda: ChromaClient().insert_data(name, description))
            # Wait for completion but don't block the main thread significantly
            future.result(timeout=30)  # 30 second timeout
            
        print(f"data '{name}'  added successfully.")
    except sqlite3.IntegrityError:
        print(f"Errr : data '{name}' already exists.")
    except Exception as e:
        print(f"Error adding embedding for '{name}': {e}")
    finally:
        conn.close()

def add_tag(name: str) -> None:
    """
    Add a new tag to the database.
    
    Inserts a new record into the tags table.
    
    Args:
        name (str): Name of the tag to add
        
    Returns:
        None
    """
    conn = sqlite3.connect(NAME_DB)
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO tags (name) VALUES (?)",
            (name,)
        )
        conn.commit()
        print(f"Tag '{name}' added successfully.")
    except sqlite3.IntegrityError:
        print(f"Error : tag '{name}' already exists.")
    finally:
        conn.close()

def add_relation(data_name: str, tag_name: str) -> None:
    """
    Create a relationship between a data item and a tag.
    
    Inserts a new record into the relation table linking data and tag.
    
    Args:
        data_name (str): Name of the data item
        tag_name (str): Name of the tag
        
    Returns:
        None
    """
    conn = sqlite3.connect(NAME_DB)
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO relation (data_name, tag_name) VALUES (?, ?)",
            (data_name, tag_name)
        )
        conn.commit()
        print(f"Relation between '{data_name}' and '{tag_name}'  added successfully.")
    except sqlite3.IntegrityError:
        print(f"Error : This relation already exists or foreign keys are unvalid.")
    finally:
        conn.close()

# REMOVE FUNCTIONS
def remove_data(name: str) -> None:
    """
    Remove a data item from the database.
    
    Deletes a record from the data table and removes the corresponding
    embedding from the ChromaClient.
    
    Args:
        name (str): Name of the data item to remove
        
    Returns:
        None
    """
    conn = sqlite3.connect(NAME_DB)
    cursor = conn.cursor()
    try:
        cursor.execute(
            "DELETE FROM data WHERE name = ?",
            (name,)
        )
        conn.commit()
        embedding = ChromaClient()
        embedding.remove_data(name)
        print(f"data '{name}' removed successfully.")
    except sqlite3.Error as e:
        print(f"Error deleting data : {e}")
    finally:
        conn.close()

def remove_tag(name: str) -> None:
    """
    Remove a tag from the database.
    
    Deletes a record from the tags table.
    
    Args:
        name (str): Name of the tag to remove
        
    Returns:
        None
    """
    conn = sqlite3.connect(NAME_DB)
    cursor = conn.cursor()
    try:
        cursor.execute(
            "DELETE FROM tags WHERE name = ?",
            (name,)
        )
        conn.commit()
        print(f"Tag '{name}' removed successfully.")
    except sqlite3.Error as e:
        print(f"Error deleting tag : {e}")
    finally:
        conn.close()

def remove_relation(data_name: str, tag_name: str) -> None:
    """
    Remove a relationship between a data item and a tag.
    
    Deletes a record from the relation table.
    
    Args:
        data_name (str): Name of the data item
        tag_name (str): Name of the tag
        
    Returns:
        None
    """
    conn = sqlite3.connect(NAME_DB)
    cursor = conn.cursor()
    try:
        cursor.execute(
            "DELETE FROM relation WHERE data_name = ? AND tag_name = ?",
            (data_name, tag_name)
        )
        conn.commit()
        
        print(f"Relation between '{data_name}' and '{tag_name}' removed successfully.")
    except sqlite3.Error as e:
        print(f"Error when deleting relation : {e}")
    finally:
        conn.close()

def update_data(name: str, description: str) -> None:
    """
    Update an existing data item in the database.
    
    Updates the description of an existing data item and updates the
    corresponding embedding in the ChromaClient.
    
    Args:
        name (str): Name of the data item to update
        description (str): New description for the data item
        
    Returns:
        None
    """
    conn = sqlite3.connect(NAME_DB)
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE data SET description = ? WHERE name = ?",
            (description, name)
        )
        conn.commit()
        
        # Run embedding update asynchronously using thread pool
        with ThreadPoolExecutor() as executor:
            future = executor.submit(lambda: ChromaClient().update_data(name, description))
            # Wait for completion but don't block the main thread significantly
            future.result(timeout=30)  # 30 second timeout
            
        print(f"data '{name}'  updated successfully.")
    except sqlite3.IntegrityError:
        print(f"Error : data '{name}' can't be updated.")
    except Exception as e:
        print(f"Error updating embedding for '{name}': {e}")
    finally:
        conn.close()

def embed_all_data() -> None:
    """
    Regenerate embeddings for all data items in the database.
    
    Retrieves all data items from the database and creates embeddings
    for each one using the ChromaClient.
    
    Returns:
        None
    """
    try:
        # Use the existing get_data() function to retrieve all data
        data_items = get_data()
        
        # Create Embedder instance
        embedding = ChromaClient()
        
        # Process all data items
        total_items = len(data_items)
        print(f"Regenerating embeddings for {total_items} data items...")
        
        for i, item in enumerate(data_items, 1):
            try:
                embedding.insert_data(item['name'], item['description'])
                print(f"Processed {i}/{total_items}: {item['name']}")
            except Exception as e:
                print(f"Error processing item '{item['name']}': {e}")
                
        print("Embedding regeneration completed successfully.")
        
    except Exception as e:
        print(f"Error in embed_all_data: {e}")
        raise

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Create user and generate Google Auth')
    parser.add_argument('-e', '--embedding', help='regenerate embeddings for chromadb', action="store_true")
    args = parser.parse_args()
    if args.embedding: 
        embed_all_data()
