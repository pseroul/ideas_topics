import re
import numpy as np
from typing import Any, List, Generator
from chromadb.utils import embedding_functions
import chromadb
from sklearn.cluster import AgglomerativeClustering
from keybert import KeyBERT
import gc

class Embedder:
    """
    A class for managing embeddings and similarity calculations using ChromaDB.
    
    This class provides functionality for storing, retrieving, and querying
    text data with semantic embeddings, including operations for inserting,
    updating, removing, and finding similar data items.
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

        self.kw_model = KeyBERT(model=self.model_name)

        
    def format_text(self, name: str, description: str) -> str:
        """
        Format text for storage in the embedding database.
        
        This method formats the name and description into a structured
        string that can be stored in the database for embedding generation.
        
        Args:
            name (str): The name/title of the data item
            description (str): The description/content of the data item
            
        Returns:
            str: Formatted string combining name and description
        """
        return f"{name}. {name}: {description}"
    
    def unformat_text(self, name: str, description: str) -> str:
        """
        Unformat text from the embedding database storage format.
        
        This method reverses the formatting applied by format_text,
        extracting the original description from the stored formatted string.
        
        Args:
            name (str): The name/title of the data item
            description (str): The formatted description from the database
            
        Returns:
            str: Extracted original description
        """
        return description.replace(f"{name}. {name}:", "")

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
            documents=[self.format_text(name, description)],
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
            documents=[self.format_text(name, description)],
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
            query_texts=[self.format_text(name, description)],
            n_results=n_results
        )
        names: list[str] = results["ids"][0]
        descriptions: list[str] = results['documents'][0]
        return [{'name': name, 'description': self.unformat_text(name, desc)} for name, desc in zip(names, descriptions)]

    def get_all_data(self) -> chromadb.GetResult:
        """
        Retrieve all data from the embedding database.
        
        Gets all documents, embeddings, and metadata from the ChromaDB collection.
        
        Returns:
            chromadb.GetResult: All data from the collection including embeddings and documents
        """
        return self.collection.get(include=['embeddings', 'documents'])
    
    def generate_toc_structure(self, max_items: int = 500) -> list:
        """
        Generate a hierarchical table of contents structure from all data.
        
        Creates a tree-like structure organizing all data items hierarchically
        based on semantic similarities using clustering techniques.
        
        Args:
            max_items (int): Maximum number of items to process to limit memory usage
            
        Returns:
            list: Hierarchical structure of data items
        """
        # Stream data in chunks to limit memory usage
        data = self.collection.get(include=['embeddings', 'documents'], limit=max_items)
        ids = data['ids']
        docs = data['documents']
        embeddings = data['embeddings']

        # Clear large data structures immediately after use
        del data
        gc.collect()
        
        toc = self._generate_toc_structure(docs, ids, embeddings)

        return toc

    def _generate_toc_structure(self, docs: list[str], ids: list[str], embeddings, level: int = 1, max_depth: int = 3) -> list[dict[str, Any]] | list[Any]:
        """
        Recursively generate a hierarchical table of contents structure.
        
        This private method creates a hierarchical organization of data items
        by applying clustering at different levels based on semantic similarities.
        
        Args:
            docs (list[str]): List of document texts
            ids (list[str]): List of document IDs
            embeddings: List of document embeddings
            level (int, optional): Current hierarchy level. Defaults to 1.
            max_depth (int, optional): Maximum recursion depth. Defaults to 3.
            
        Returns:
            list[dict[str, Any]] | list[Any]: Hierarchical structure at current level
        """
        X = np.array(embeddings)

        if len(X) <= 2 or level > max_depth:
            # Create entries with originality scores for leaf nodes
            entries = [{"title": id, "text": doc, "type": "idea", "id": id} for doc, id in zip(docs, ids)]
            return entries

        n_clusters = max(2, int(np.sqrt(len(X))))

        clustering = AgglomerativeClustering(
            n_clusters=n_clusters,
            metric='cosine',
            linkage='average'
        )
        labels = clustering.fit_predict(X)

        toc = []
        for label in np.unique(labels):
            indices = np.where(labels == label)[0]

            cluster_embeddings = [embeddings[i] for i in indices]
            cluster_docs = [docs[i] for i in indices]
            cluster_ids = [ids[i] for i in indices]

            title_text = self.generate_synthetic_title(cluster_docs)

            children = self._generate_toc_structure(
                cluster_docs,
                cluster_ids,
                cluster_embeddings,
                level + 1,
                max_depth
            )

            heading_entry = {
                "title": title_text,
                "type": "heading",
                "level": level,
                "children": children,
            }
                        
            toc.append(heading_entry)

        return toc
    
    def generate_synthetic_title(self, cluster_docs: list[str]) -> str:
        """
        Extracts the most representative keywords to form a coherent 2-3 word title.
        
        This method analyzes a cluster of document texts and generates a synthetic
        title by extracting the most representative keywords using KeyBERT topic modeling.
        The resulting title combines 1-2 keywords into a coherent phrase suitable for
        hierarchical organization.
        
        Args:
            cluster_docs (list[str]): A list of document texts belonging to the same cluster.
                Each document should be a string containing the content to analyze.
                
        Returns:
            str: A generated title consisting of 1-2 representative keywords joined by "&".
                Returns "Untitled Section" if the input list is empty.
                Returns "General Topic" if keyword extraction fails.
                Returns a fallback title based on the first document if all else fails.
        """
        if not cluster_docs:
            return "Untitled Section"
        
        # Combine documents into a single text block
        # We clean basic punctuation to help keyword extraction
        full_text = " ".join([re.sub(r'[^\w\s]', '', doc.lower()) for doc in cluster_docs])

        try:
            # Extract keywords
            keywords = self.kw_model.extract_keywords(
                full_text, 
                keyphrase_ngram_range=(1, 2), 
                stop_words='english',
                use_mmr=True, # Diversifies the result to avoid redundancy
                diversity=0.7,
                top_n=2
            )

            if not keywords:
                return "General Topic"

            # We take the top 1 or 2 results and format them
            # Result format is [('keyword', score), ...]
            title_parts = [k[0] for k in keywords]
            
            # Create a title from the top 1 or 2 phrases
            final_title = " & ".join(title_parts).title()
            
            return final_title

        except Exception:
            return "Section: " + cluster_docs[0][:20].title()
