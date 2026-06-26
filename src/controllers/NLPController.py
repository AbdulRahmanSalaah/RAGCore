from .BaseController import BaseController
from models.db_schemes import Project , DataChunk
from stores.llm.LLMEnums import DocumentTypeEnum
from typing import List
import json

class NLPController(BaseController):
    def __init__(self, vectordb_client ,generation_client,embedding_client, project_id: str):
        super().__init__()
        self.vectordb_client  = vectordb_client 
        self.generation_client = generation_client
        self.embedding_client = embedding_client
        
        # Calculate the collection name ONCE when the controller is created
        self.project_id = project_id
        self.collection_name = f"collection_{project_id}".strip()
    
    def reset_vector_db_collection(self):
        return self.vectordb_client.delete_collection(collection_name=self.collection_name)   
    
    
    def get_vector_db_collection_info(self):
        collection_info = self.vectordb_client.get_collection_info(collection_name=self.collection_name)

        return json.loads(
            json.dumps(collection_info, default=lambda x: x.__dict__)
        )
        
        
    def index_into_vector_db(self, chunks: List[DataChunk],
                                   do_reset: bool = False):
        
        # manage items
        texts_to_embed = [c.chunk_text for c in chunks]
        
        # Inject MongoDB _id into metadata so it can be retrieved later from Qdrant
        metadata = []
        for c in chunks:
            meta = c.chunk_metadata.copy()
            meta["chunk_id"] = str(c.id) if c.id else None
            metadata.append(meta)
            
        vectors = [
            self.embedding_client.embed_text(
                text=text, 
                document_type=DocumentTypeEnum.DOCUMENT.value)
            for text in texts_to_embed
        ]
       
        # create collection if not exists
        _ = self.vectordb_client.create_collection(
            collection_name=self.collection_name,
            embedding_size=self.embedding_client.embedding_size,
            do_reset=do_reset,
        )
       
        # insert into vector db
        _ = self.vectordb_client.insert_many(
            collection_name=self.collection_name,
            texts=texts_to_embed,
            metadata=metadata,
            vectors=vectors,
        )
        
        return True
    
    
    
    def search_vector_db_collection(self, text: str, limit: int = 10):
        
        vector = self.embedding_client.embed_text(
            text=text,
            document_type=DocumentTypeEnum.QUERY.value
        )
        
        if not vector or len(vector) == 0:
            return False
        
        results = self.vectordb_client.search_by_vector(
            collection_name=self.collection_name,
            vector=vector,
            limit=limit,
        )
        
        if not results:
            return False
        
        return results