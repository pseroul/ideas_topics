import chromadb
import re
from chromadb.utils import embedding_functions
from typing import Any
import numpy as np
from sklearn.cluster import AgglomerativeClustering
from sklearn.feature_extraction.text import TfidfVectorizer

class Embedder: 
    """
    A class for managing embeddings and similarity calculations using ChromaDB.
    
    This class provides functionality for storing, retrieving, and querying
    text data with semantic embeddings, including operations for inserting,
    updating, removing, and finding similar data items.
    """

    def __init__(self, db_path: str="./data/embeddings", collection_name: str = "Ideas_topics") -> None:
        """
        Initialize the Embedder with a ChromaDB client and collection.
        
        Args:
            db_path (str, optional): Path to the ChromaDB persistent client storage.
                Defaults to "./data/embeddings".
            collection_name (str, optional): Name of the ChromaDB collection to use.
                Defaults to "Ideas_topics".
        """
        self.client = chromadb.PersistentClient(path=db_path)
        self.emb_fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-distilroberta-v1")
        self.collection = self.client.get_or_create_collection(
            name=collection_name, 
            embedding_function=self.emb_fn
        )
        
    def _format_text(self, name: str, description: str) -> str:
        """
        Format text for storage in the embedding database.
        
        This private method formats the name and description into a structured
        string that can be stored in the database for embedding generation.
        
        Args:
            name (str): The name/title of the data item
            description (str): The description/content of the data item
            
        Returns:
            str: Formatted string combining name and description
        """
        return f"{name}. {name}: {description}"
    
    def _unformat_text(self, name: str, description: str) -> str:
        """
        Unformat text from the embedding database storage format.
        
        This private method reverses the formatting applied by _format_text,
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
        self.collection.add(documents=[self._format_text(name, description)], 
                            metadatas=[{"name": name}],
                            ids=[name])     

    def update_data(self, name: str, description: str) -> None:
        """
        Update existing data in the embedding database.
        
        Updates an existing document in the ChromaDB collection with new
        content while preserving the existing ID.
        
        Args:
            name (str): The name/title of the data item to update
            description (str): The new description/content for the data item
        """
        self.collection.update(documents=[self._format_text(name, description)], 
                            metadatas=[{"name": name}], 
                            ids=[name])
        
    def remove_data(self, name: str) -> None: 
        """
        Remove data from the embedding database.
        
        Deletes a document from the ChromaDB collection based on its ID.
        
        Args:
            name (str): The name/title of the data item to remove
        """
        self.collection.delete(ids=[name])
        
    def get_similar_data(self, name: str, description: str, n_results: int=10) -> list[dict[str, str]]:
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
            query_texts=[self._format_text(name, description)], 
            n_results = n_results)
        names: list[str] = results["ids"][0]
        descriptions = results['documents'][0]
        return [{'name': name, 'description': self._unformat_text(name, desc)} for name, desc in zip(names, descriptions)]

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
        embeddings: chromadb.Embeddings = data['embeddings']

        return self._generate_toc_structure(docs, ids, embeddings)

    def _generate_toc_structure(self, docs: list[str], ids: list[str], embeddings: chromadb.Embeddings, level: int=1, max_depth: int=3) -> list[dict[str, Any]] | list[Any]:
        """
        Recursively generate a hierarchical table of contents structure.
        
        This private method creates a hierarchical organization of data items
        by applying clustering at different levels based on semantic similarities.
        
        Args:
            docs (list[str]): List of document texts
            ids (list[str]): List of document IDs
            embeddings (chromadb.Embeddings): List of document embeddings
            level (int, optional): Current hierarchy level. Defaults to 1.
            max_depth (int, optional): Maximum recursion depth. Defaults to 3.
            
        Returns:
            list[dict[str, Any]] | list[Any]: Hierarchical structure at current level
        """
        X = np.array(embeddings)
    
        # Condition d'arrêt : si peu d'idées ou profondeur max atteinte
        if len(X) <= 2 or level > max_depth:
            return [{"title": id, "text": doc, "type": "idea", "id": id} for doc, id in zip(docs, ids)]

        # Calcul du nombre de clusters pour ce niveau
        # On divise par 2 ou 3 pour créer des groupes digestes
        n_clusters = max(2, int(np.sqrt(len(X))))
        
        # Clustering pour ce niveau
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

            # --- NOUVEAUTÉ : Génération du titre synthétique ---
            title_text = self.generate_synthetic_title(cluster_docs)
            
            # Pour le contenu, on garde toutes les idées
            children = self._generate_toc_structure(
                cluster_docs, 
                cluster_ids, 
                cluster_embeddings, 
                level + 1, 
                max_depth
            )
            
            toc.append({
                "title": title_text,
                "type": "heading",
                "level": level,
                "children": children
            })

        return toc
    
    def generate_synthetic_title(self, cluster_docs: list[str]) -> str:
        """
        Generate a synthetic title from a cluster of ideas using TF-IDF analysis.
        
        This method analyzes a group of related documents to extract the most
        significant terms and create a coherent, descriptive title that represents
        the semantic content of the cluster.
        
        Args:
            cluster_docs (list[str]): List of document texts in the cluster
            
        Returns:
            str: Generated synthetic title for the cluster
        """
        if not cluster_docs:
            return "New Section"
        
        clean_docs = [re.sub(r'[^\w\s]', ' ', doc.lower()) for doc in cluster_docs]

        try:
            # On extrait un peu plus de termes pour avoir du choix après filtrage
            vectorizer = TfidfVectorizer(
                stop_words='english', 
                ngram_range=(1, 2), 
                max_features=30 
            )
            
            tfidf_matrix = vectorizer.fit_transform(clean_docs)
            scores = np.asarray(tfidf_matrix.sum(axis=0)).flatten()
            terms = vectorizer.get_feature_names_out()
            
            # Tri des termes par score TF-IDF décroissant
            sorted_indices = np.argsort(scores)[::-1]
            sorted_terms = [terms[i] for i in sorted_indices]
            
            final_selection = []
            
            for term in sorted_terms:
                # Sécurité : On limite à 2 ou 3 concepts clés pour le titre
                if len(final_selection) >= 2:
                    break
                
                # On vérifie si les mots du terme actuel sont déjà présents 
                # dans les termes déjà sélectionnés (et inversement)
                words_in_term = set(term.split())
                is_redundant = False
                
                for selected in final_selection:
                    words_in_selected = set(selected.split())
                    # Si intersection non vide (ex: 'hardware' et 'hardware recommendation')
                    if words_in_term.intersection(words_in_selected):
                        is_redundant = True
                        break
                
                if not is_redundant:
                    final_selection.append(term)

            # Mise en forme
            title = " & ".join([t.capitalize() for t in final_selection])
            
            return title if len(title) > 2 else "Divers & " + cluster_docs[0][:20]

        except Exception:
            return "Section : " + cluster_docs[0][:30] + "..."
