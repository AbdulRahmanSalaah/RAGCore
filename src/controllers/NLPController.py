from .BaseController import BaseController
from models.db_schemes import Project , DataChunk
from stores.llm.LLMEnums import DocumentTypeEnum
from typing import List
import json

from stores.llm.templates.template_parser import TemplateParser



class NLPController(BaseController):
    def __init__(self, vectordb_client ,generation_client,embedding_client, template_parser, project_id: str):
        super().__init__()
        self.vectordb_client  = vectordb_client 
        self.generation_client = generation_client
        self.embedding_client = embedding_client
        self.template_parser = template_parser
        
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
    
    
    def answer_rag_question(self, query: str, limit: int = 10):
        
        answer, full_prompt, chat_history = None, None, None
        
        # step1: retrieve related documents
        retrieved_documents = self.search_vector_db_collection(
            text=query,
            limit=limit,
        )
        
        if not retrieved_documents or len(retrieved_documents) == 0:
            return answer, full_prompt, chat_history
        
        
        
        # step2: Construct LLM prompt
        system_prompt = self.template_parser.get("rag", "system_prompt")
        
        
        
        documents_prompts = "\n".join([
            self.template_parser.get("rag", "document_prompt", {
                    "doc_num": idx + 1,
                    "chunk_text": doc.text,
            })
            for idx, doc in enumerate(retrieved_documents)
        ])
        
        
        

        footer_prompt = self.template_parser.get("rag", "footer_prompt", {
            "query": query,
        })
        

        # step3: Construct Generation Client Prompts
        chat_history = []

        full_prompt = "\n\n".join([ documents_prompts,  footer_prompt])

        # step4: Retrieve the Answer
        answer = self.generation_client.generate_text(
            prompt=full_prompt,
            system_prompt=system_prompt,
            chat_history=chat_history
        )

        return answer, full_prompt, chat_history
    
    
    
    