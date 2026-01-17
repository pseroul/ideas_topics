import chromadb
import re
from chromadb.utils import embedding_functions
from typing import Any
import numpy as np
from sklearn.cluster import AgglomerativeClustering
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

    def _generate_toc_structure(self, docs: list[str], ids: list[str], embeddings, level: int=1, max_depth: int=3) -> list[dict[str, Any]] | list[Any]:
    
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
            
            node_type = "heading" if level <= 2 else "content"
            
            toc.append({
                "title": title_text,
                "type": node_type,
                "level": level,
                "children": children
            })

        return toc
    
    def generate_synthetic_title(self, cluster_docs: list[str]) -> str:
        """
        Generate synthetic title from a cluster of ideas.
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