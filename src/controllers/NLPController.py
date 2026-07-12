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
        self.collection_name = f"collection_{vectordb_client.default_vector_size}_{project_id}".strip()
    
    async def reset_vector_db_collection(self):
        return await self.vectordb_client.delete_collection(collection_name=self.collection_name)   
    
    
    async def get_vector_db_collection_info(self):
        collection_info = await self.vectordb_client.get_collection_info(collection_name=self.collection_name)

        return json.loads(
            json.dumps(collection_info, default=lambda x: x.__dict__)
        )
        
        
    async def index_into_vector_db(self, chunks: List[DataChunk]):

        
        # manage items
        texts_to_embed = [c.chunk_text for c in chunks]
        
        # Inject chunk integer PK into metadata so it can be retrieved from the vector store later
        metadata = []
        for c in chunks:
            meta = c.chunk_metadata.copy()
            meta["chunk_id"] = str(c.id) if c.id else None
            metadata.append(meta)
            
        vectors = self.embedding_client.embed_text(
            text=texts_to_embed,
            document_type=DocumentTypeEnum.DOCUMENT.value
        )


        # extract chunk integer PKs for PGVector's FOREIGN KEY column
        record_ids = [c.id for c in chunks]

        # insert into vector db
        _ = await self.vectordb_client.insert_many(
            collection_name=self.collection_name,
            texts=texts_to_embed,
            metadata=metadata,
            vectors=vectors,
            record_ids=record_ids,
        )

        
        return True
    
    
    
    async def search_vector_db_collection(self, text: str, limit: int = 10):
        
        # embed_text now returns a list of vectors; take the first one for a single query
        vectors = self.embedding_client.embed_text(
            text=text,
            document_type=DocumentTypeEnum.QUERY.value
        )
        
        if not vectors or len(vectors) == 0:
            return False
        
        vector = vectors[0]

        results = await self.vectordb_client.search_by_vector(
            collection_name=self.collection_name,
            vector=vector,
            limit=limit,
        )
        
        if not results:
            return False
        
        return results
    
    
    async def answer_rag_question(self, query: str, limit: int = 10):
        
        answer, full_prompt, chat_history = None, None, None
        
        # step1: retrieve related documents
        retrieved_documents = await self.search_vector_db_collection(
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
                    "chunk_text": self.generation_client.process_text(doc.text),
            })
            for idx, doc in enumerate(retrieved_documents)
        ])
        
        
        

        footer_prompt = self.template_parser.get("rag", "footer_prompt", {
            "query": query,
        })
        

        # step3: Construct Generation Client Prompts
        chat_history = [
            self.generation_client.construct_prompt(
                prompt=system_prompt,
                role=self.generation_client.enums.SYSTEM.value,
            )
        ]

        full_prompt = "\n\n".join([ documents_prompts,  footer_prompt])

        # step4: Retrieve the Answer
        answer = self.generation_client.generate_text(
            prompt=full_prompt,
            chat_history=chat_history
        )

        return answer, full_prompt, chat_history
    
    
