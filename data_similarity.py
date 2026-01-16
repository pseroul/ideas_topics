import chromadb
from chromadb.utils import embedding_functions
from typing import Any
import numpy as np
from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer

class Embeddings: 
    def __init__(self, db_path="./data/embeddings", collection_name = "Ideas_topics") -> None:
        self.client = chromadb.PersistentClient(path=db_path)
        self.emb_fn = embedding_functions.DefaultEmbeddingFunction()
        self.collection = self.client.get_or_create_collection(
            name=collection_name, 
            embedding_function=self.emb_fn
        )
        
    def _format_text(self, name: str, description: str) -> str:
        return f"{name}. {name}: {description}"
    
    def _unformat_text(self, name: str, description: str) -> str:
        return description.replace(f"{name}. {name}:", "")

    def insert_data(self, name: str, description: str) -> None:
        self.collection.add(documents=[self._format_text(name, description)], 
                            metadatas=[{"name": name}],
                            ids=[name])     

    def update_data(self, name: str, description: str) -> None:
        self.collection.update(documents=[self._format_text(name, description)], 
                            metadatas=[{"name": name}], 
                            ids=[name])
        
    def remove_data(self, name: str): 
        self.collection.delete(ids=[name])
        
    def get_similar_data(self, name: str, description: str, n_results: int=10) -> list[dict[str, str]]:
        if n_results == 0:
            return []
        results = self.collection.query(
            query_texts=[self._format_text(name, description)], 
            n_results = n_results)
        names: list[str] = results["ids"][0]
        descriptions = results['documents'][0]
        return [{'name': name, 'description': self._unformat_text(name, desc)} for name, desc in zip(names, descriptions)]

    def get_all_data(self) -> chromadb.GetResult:
        return self.collection.get(include=['embeddings', 'documents'])
    
    def generate_toc_structure(self) -> list[dict[str, Any]] | list[Any]:

        data = self.collection.get(include=['embeddings', 'documents'])
        ids = data['ids']
        docs = data['documents']
        embeddings = data['embeddings']

        return self._generate_toc_structure(docs, ids, embeddings)

    def _generate_toc_structure(self, docs, ids, embeddings, level=1, max_depth=3) -> list[dict[str, Any]] | list[Any]:
    
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
            
            # Pour le contenu, on garde toutes les idées (on ne retire plus le centroïde)
            children = self._generate_toc_structure(
                cluster_docs, 
                cluster_ids, 
                cluster_embeddings, 
                level + 1, 
                max_depth
            )
            
            node_type = "chapter" if level == 1 else "section"
            
            toc.append({
                "title": title_text,
                "type": node_type,
                "level": level,
                "children": children
            })

        return toc
    
    def generate_synthetic_title(self, cluster_docs) -> str:
        """
        Génère un titre basé sur les mots-clés les plus pertinents du groupe.
        """
        if not cluster_docs:
            return "Section sans titre"
        
        # On utilise TF-IDF pour trouver les mots qui caractérisent le mieux ce groupe
        # stop_words='french' (ou 'english') permet d'ignorer les mots inutiles (le, la, de...)
        vectorizer = TfidfVectorizer(stop_words='english', max_features=10)
        
        try:
            tfidf_matrix = vectorizer.fit_transform(cluster_docs)
            # Somme des scores TF-IDF pour chaque mot sur l'ensemble du cluster
            scores = np.asarray(tfidf_matrix.sum(axis=0)).flatten()
            words = vectorizer.get_feature_names_out()
            print("generate_synthetic_title:", words)
            
            # On trie pour avoir les meilleurs mots en premier
            important_indices = np.argsort(scores)[::-1][:3]
            top_words = [words[i].capitalize() for i in important_indices]
            
            return " & ".join(top_words)
        except:
            # Cas de secours si le cluster est trop petit ou composé uniquement de stop-words
            return cluster_docs[0][:50] + "..."