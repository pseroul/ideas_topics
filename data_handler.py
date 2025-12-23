import sqlite3
from typing import Any, Hashable
import pandas as pd

# Nom de la base de datas
NAME_DB = "data/knowledge.db"

def init_database() -> None:
    print("init_database")
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

def get_data_from_tags(tags: str) -> list[dict[Hashable, Any]]:
    print("get_data_from_tags", tags)
    if not tags:
        return get_data()
    else:
        tags_list = tags.split(";")
        print(tags_list)
        placeholders = ", ".join(["?"] * len(tags_list))
        conn = sqlite3.connect(NAME_DB)
        query = f"""
        SELECT DISTINCT d.name, d.description
        FROM data d
        JOIN relation r ON d.name = r.data_name
        JOIN tags t ON r.tag_name = t.name
        WHERE t.name IN ({placeholders});
        """
        print(query)
        df = pd.read_sql_query(query, conn, params=tags_list)
        conn.close()
    return df.to_dict("records")


def get_data() -> list[dict[Hashable, Any]]:
    conn = sqlite3.connect(NAME_DB)
    df = pd.read_sql_query("SELECT * FROM data", conn)
    conn.close()
    return df.to_dict("records")

def get_tags() -> list[dict[Hashable, Any]]:
    conn = sqlite3.connect(NAME_DB)
    df = pd.read_sql_query("SELECT * FROM tags", conn)
    conn.close()
    return df.to_dict("records")

def get_relations() -> list[dict[Hashable, Any]]:
    conn = sqlite3.connect(NAME_DB)
    df = pd.read_sql_query("SELECT * FROM relation", conn)
    conn.close()
    return df.to_dict("records")

def add_data(name: str, description: str) -> None:
    conn = sqlite3.connect(NAME_DB)
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO data (name, description) VALUES (?, ?)",
            (name, description)
        )
        conn.commit()
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
        print(f"Erreur : This relation already exists or foreign keys are unvalid.")
    finally:
        conn.close()

# Fonctions de suppression
def remove_data(name: str) -> None:
    conn = sqlite3.connect(NAME_DB)
    cursor = conn.cursor()
    try:
        cursor.execute(
            "DELETE FROM data WHERE name = ?",
            (name,)
        )
        conn.commit()
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



