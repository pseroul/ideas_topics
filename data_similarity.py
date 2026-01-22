import re
import numpy as np
from typing import Any, List
from chromadb.utils import embedding_functions
import chromadb
from sklearn.cluster import AgglomerativeClustering
from keybert import KeyBERT

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
    
    def generate_toc_structure(self) -> list[dict[str, Any]] | list[Any]:
        """
        Generate a hierarchical table of contents structure from all data.
        
        Creates a tree-like structure organizing all data items hierarchically
        based on semantic similarities using clustering techniques.
        
        Returns:
            list[dict[str, Any]] | list[Any]: Hierarchical structure of data items
        """
        data = self.collection.get(include=['embeddings', 'documents'])
        ids = data['ids']
        docs = data['documents']
        embeddings: List[List[float]] = data['embeddings']

        return self._generate_toc_structure(docs, ids, embeddings)

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
            # Calculate originality scores for all entries
            self._calculate_originality_scores(entries, embeddings)
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

            # Create heading entry with originality score
            heading_entry = {
                "title": title_text,
                "type": "heading",
                "level": level,
                "children": children
            }
            
            # Calculate originality score for this heading
            self._calculate_heading_originality_score(heading_entry, embeddings, docs, ids)
            
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

    def _calculate_originality_scores(self, entries: list[dict[str, Any]], embeddings: List[List[float]]) -> None:
        """
        Calculate originality scores for all entries based on their distance to k nearest neighbors.
        
        Args:
            entries (list[dict[str, Any]]): List of TOC entries to calculate scores for
            embeddings (List[List[float]]): List of document embeddings
        """
        if len(entries) <= 1:
            # If there's only one entry or none, set score to 1.0 (most original)
            for entry in entries:
                entry["originality_score"] = 1.0
            return
            
        # Convert embeddings to numpy array for distance calculations
        X = np.array(embeddings)
        n_entries = len(X)
        k = min(5, n_entries - 1)  # Use minimum of 5 or (total_entries - 1)
        
        # For each entry, calculate distances to all others and find k nearest
        scores = []
        for i in range(n_entries):
            # Calculate distances to all other entries
            distances = []
            for j in range(n_entries):
                if i != j:
                    # Calculate cosine distance
                    dot_product = np.dot(X[i], X[j])
                    norm_i = np.linalg.norm(X[i])
                    norm_j = np.linalg.norm(X[j])
                    if norm_i > 0 and norm_j > 0:
                        cos_sim = dot_product / (norm_i * norm_j)
                        cos_dist = 1 - cos_sim
                        distances.append(cos_dist)
                    else:
                        # If one vector is zero, set distance to maximum
                        distances.append(1.0)
            
            if len(distances) > 0:
                # Use argpartition for better performance when we only need k smallest values
                if k > 0 and len(distances) > k:
                    # Get indices of k smallest distances
                    nearest_indices = np.argpartition(distances, k)[:k]
                    k_nearest_distances = [distances[idx] for idx in nearest_indices]
                else:
                    k_nearest_distances = distances[:k] if k > 0 else distances
                
                # Average distance to k nearest neighbors
                avg_distance = np.mean(k_nearest_distances)
                # Convert to originality score (higher distance = more original)
                # Normalize to 0-1 scale where 1 is most original
                originality_score = 1.0 - (avg_distance / (1.0 + 1e-8))
                # Ensure score is between 0 and 1
                originality_score = max(0.0, min(1.0, originality_score))
                scores.append(originality_score)
            else:
                scores.append(1.0)
        
        # Assign scores to entries
        for i, entry in enumerate(entries):
            entry["originality_score"] = scores[i]

    def _calculate_heading_originality_score(self, heading_entry: dict[str, Any], all_embeddings: List[List[float]], all_docs: list[str], all_ids: list[str]) -> None:
        """
        Calculate originality score for a heading entry based on its children and the overall dataset.
        
        Args:
            heading_entry (dict[str, Any]): The heading entry to calculate score for
            all_embeddings (List[List[float]]): All document embeddings
            all_docs (list[str]): All document texts
            all_ids (list[str]): All document IDs
        """
        # Get all child entries to calculate their embeddings
        def collect_child_embeddings(entry, child_embeddings, child_docs, child_ids):
            """Recursively collect embeddings from all children."""
            if entry.get("type") == "idea":
                # This is a leaf node
                try:
                    idx = all_ids.index(entry["id"])
                    child_embeddings.append(all_embeddings[idx])
                    child_docs.append(all_docs[idx])
                    child_ids.append(entry["id"])
                except ValueError:
                    # If ID not found, skip this entry
                    pass
            elif entry.get("children"):
                # This is a heading with children
                for child in entry["children"]:
                    collect_child_embeddings(child, child_embeddings, child_docs, child_ids)
        
        # Collect all child data
        child_embeddings = []
        child_docs = []
        child_ids = []
        
        if "children" in heading_entry:
            for child in heading_entry["children"]:
                collect_child_embeddings(child, child_embeddings, child_docs, child_ids)
        
        # If we have child data, calculate originality based on children vs rest of dataset
        if len(child_embeddings) > 0 and len(all_embeddings) > 0:
            # Calculate average embedding for this heading's children
            avg_child_embedding = np.mean(child_embeddings, axis=0)
            
            # Convert all_embeddings to numpy array for efficient computation
            all_emb_array = np.array(all_embeddings)
            
            # Create mask for non-child entries
            child_id_set = set(child_ids)
            non_child_mask = [i for i, emb_id in enumerate(all_ids) if emb_id not in child_id_set]
            
            if len(non_child_mask) > 0:
                # Get embeddings of non-child entries
                non_child_embeddings = all_emb_array[non_child_mask]
                
                # Calculate cosine distances efficiently using vectorized operations
                # Normalize the embeddings for cosine similarity calculation
                norm_child = np.linalg.norm(avg_child_embedding)
                norm_non_child = np.linalg.norm(non_child_embeddings, axis=1)
                
                # Avoid division by zero
                norm_child = norm_child if norm_child > 0 else 1e-8
                norm_non_child = np.where(norm_non_child == 0, 1e-8, norm_non_child)
                
                # Calculate cosine similarities
                dot_products = np.dot(non_child_embeddings, avg_child_embedding)
                cos_similarities = dot_products / (norm_non_child * norm_child)
                
                # Convert to cosine distances
                cos_distances = 1 - cos_similarities
                
                # Use k nearest neighbors (k=5) for heading score calculation
                k = min(5, len(cos_distances))
                if k > 0 and len(cos_distances) > 0:
                    # Use argpartition for better performance
                    # Ensure k is within valid bounds for argpartition
                    if len(cos_distances) > 1:
                        k = min(k, len(cos_distances) - 1)
                        nearest_indices = np.argpartition(cos_distances, k)[:k]
                        k_nearest_distances = cos_distances[nearest_indices]
                        # Average distance to k nearest neighbors
                        avg_distance = float(np.mean(k_nearest_distances))
                    else:
                        # If only one distance, use that distance
                        avg_distance = float(cos_distances[0]) if len(cos_distances) > 0 else 0.0
                else:
                    avg_distance = 0.0
                
                # Convert to originality score
                originality_score = 1.0 - (avg_distance / (1.0 + 1e-8))
                # Ensure score is between 0 and 1
                originality_score = max(0.0, min(1.0, originality_score))
                heading_entry["originality_score"] = originality_score
            else:
                # If no other entries, this is very original
                heading_entry["originality_score"] = 1.0
        else:
            # Fallback: if no children or no embeddings, set to 1.0
            heading_entry["originality_score"] = 1.0
