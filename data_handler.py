import sqlite3
from typing import Any, Hashable
import pandas as pd
from data_similarity import Embeddings
from config import NAME_DB


def init_database() -> None:
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
def get_data_from_tags(tags: str) -> list[dict[Hashable, str]]:
    if not tags:
        return get_data()
    else:
        tags_list = tags.split(";")
        placeholders = ", ".join(["?"] * len(tags_list))
        conn = sqlite3.connect(NAME_DB)
        query = f"""
        SELECT DISTINCT d.name, d.description
        FROM data d
        JOIN relation r ON d.name = r.data_name
        JOIN tags t ON r.tag_name = t.name
        WHERE t.name IN ({placeholders});
        """
        df = pd.read_sql_query(query, conn, params=tags_list)
        conn.close()
    return df.to_dict("records")

def get_data() -> list[dict[Hashable, Any]]:
    conn = sqlite3.connect(NAME_DB)
    df = pd.read_sql_query("SELECT * FROM data", conn)
    df['id'] = df['name']
    conn.close()
    return df.to_dict("records")

def get_selected_data(subname: str) -> list[dict[Hashable, Any]]:
    subname = "%" + subname + "%"
    conn = sqlite3.connect(NAME_DB)
    df = pd.read_sql_query("SELECT * FROM data WHERE name LIKE (?)", conn, params=[subname])
    df['id'] = df['name']
    conn.close()
    return df.to_dict("records")

def get_description(data_name: str) -> str:
    conn = sqlite3.connect(NAME_DB)
    df = pd.read_sql_query("SELECT description FROM data WHERE name=(?)", conn, params=[data_name])
    conn.close()
    return df['description'].iloc[0]

def get_tags() -> list[dict[Hashable, Any]]:
    conn = sqlite3.connect(NAME_DB)
    df = pd.read_sql_query("SELECT * FROM tags", conn)
    conn.close()
    return df.to_dict("records")

def get_tags_from_data(data: str):
    if not data:
        return get_tags()
    else:
        conn = sqlite3.connect(NAME_DB)
        query = "SELECT tag_name FROM relation WHERE data_name = (?)"
        df = pd.read_sql_query(query, conn, params=[data])
        conn.close()
    return df['tag_name'].to_list()

def get_similar_data(data: str) -> None:
    conn = sqlite3.connect(NAME_DB)
    query = "SELECT name, description FROM data WHERE name = (?)"
    df = pd.read_sql_query(query, conn, params=[data])
    embedding = Embeddings()
    results = embedding.get_similar_data(df['name'], df['description'])
    conn.close()
    return results

# ADD FUNCTIONS
def add_data(name: str, description: str) -> None:
    conn = sqlite3.connect(NAME_DB)
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO data (name, description) VALUES (?, ?)",
            (name, description)
        )
        conn.commit()
        embedding = Embeddings()
        embedding.insert_data(name, description)
        print(f"data '{name}'  added successfully.")
    except sqlite3.IntegrityError:
        print(f"Errr : data '{name}' already exists.")
    finally:
        conn.close()

def add_tag(name: str) -> None:
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
    conn = sqlite3.connect(NAME_DB)
    cursor = conn.cursor()
    try:
        cursor.execute(
            "DELETE FROM data WHERE name = ?",
            (name,)
        )
        conn.commit()
        embedding = Embeddings()
        embedding.remove_data(name)
        print(f"data '{name}' removed successfully.")
    except sqlite3.Error as e:
        print(f"Error deleting data : {e}")
    finally:
        conn.close()

def remove_tag(name: str) -> None:
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


# UPDATE FUNCTIONS
def update_data(name: str, description: str) -> None:
    conn = sqlite3.connect(NAME_DB)
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE data SET description = ? WHERE name = ?",
            (description, name)
        )
        conn.commit()
        embedding = Embeddings()
        embedding.update_data(name, description)
        print(f"data '{name}'  updated successfully.")
    except sqlite3.IntegrityError:
        print(f"Error : data '{name}' can't be updated.")
    finally:
        conn.close()

def embed_all_data() -> None:
    conn = sqlite3.connect(NAME_DB)    
    df = pd.read_sql_query("SELECT * FROM data", conn)
    embedding = Embeddings()
    for _, row in df.iterrows():
        embedding.insert_data(row['name'], row['description'])
    conn.close()
