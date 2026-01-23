
import chromadb
from chromadb.utils import embedding_functions
import utils

class ChromaClient:
    """
    A class for managing embeddings and similarity calculations using ChromaDB.
    
    Provides functionality for storing, retrieving, and querying text data with
    semantic embeddings, including operations for inserting, updating, removing,
    and finding similar data items.
    """

    def __init__(self, db_path: str = "./data/embeddings", collection_name: str = "Ideas_topics") -> None:
        """
        Initialize the Embedder with a ChromaDB client and collection.
        
        Args:
            db_path (str, optional): Path to the ChromaDB persistent client storage.
                Defaults to "./data/embeddings".
            collection_name (str, optional): Name of the ChromaDB collection to use.
                Defaults to "Ideas_topics".
        """
        self.model_name = "all-distilroberta-v1"
        self.client = chromadb.PersistentClient(path=db_path)
        self.emb_fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=self.model_name)
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=self.emb_fn
        )

    def insert_data(self, name: str, description: str) -> None:
        """
        Insert new data into the embedding database.
        
        Adds a new document to the ChromaDB collection with the provided
        name and description, formatted appropriately for embedding.
        
        Args:
            name (str): The name/title of the data item to insert
            description (str): The description/content of the data item to insert
        """
        self.collection.add(
            documents=[utils.format_text(name, description)],
            metadatas=[{"name": name}],
            ids=[name]
        )

    def update_data(self, name: str, description: str) -> None:
        """
        Update existing data in the embedding database.
        
        Updates an existing document in the ChromaDB collection with new
        content while preserving the existing ID.
        
        Args:
            name (str): The name/title of the data item to update
            description (str): The new description/content for the data item
        """
        self.collection.update(
            documents=[utils.format_text(name, description)],
            metadatas=[{"name": name}],
            ids=[name]
        )
        
    def remove_data(self, name: str) -> None:
        """
        Remove data from the embedding database.
        
        Deletes a document from the ChromaDB collection based on its ID.
        
        Args:
            name (str): The name/title of the data item to remove
        """
        self.collection.delete(ids=[name])
        
    def get_similar_data(self, name: str, description: str, n_results: int = 10) -> list[dict[str, str]]:
        """
        Find similar data items based on semantic similarity.
        
        Performs a semantic search in the ChromaDB collection to find
        data items similar to the provided query.
        
        Args:
            name (str): The name/title of the query item
            description (str): The description/content of the query item
            n_results (int, optional): Number of similar results to return.
                Defaults to 10.
                
        Returns:
            list[dict[str, str]]: List of dictionaries containing 'name' and 'description'
                of similar data items
        """
        if n_results == 0:
            return []
        results = self.collection.query(
            query_texts=[utils.format_text(name, description)],
            n_results=n_results
        )
        names: list[str] = results["ids"][0]
        descriptions: list[str] = results['documents'][0]
        return [{'name': name, 'description': utils.unformat_text(name, desc)} for name, desc in zip(names, descriptions)]

    def get_all_data(self, max_items: int = 500) -> chromadb.GetResult:
        """
        Retrieve all data from the embedding database.
        
        Gets all documents, embeddings, and metadata from the ChromaDB collection.
        
        Returns:
            chromadb.GetResult: All data from the collection including embeddings and documents
        """
        return self.collection.get(include=['embeddings', 'documents'], limit=max_items)
