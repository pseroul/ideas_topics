import chromadb
from chromadb.utils import embedding_functions
from typing import Hashable

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