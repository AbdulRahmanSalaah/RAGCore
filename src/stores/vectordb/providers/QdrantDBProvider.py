from ..VectorDBInterface import VectorDBInterface
from ..VectorDBEnums import DistanceMethodEnums 
from qdrant_client import models, QdrantClient
from models.db_schemes import RetrievedDocument

import logging
from typing import List



class QdrantDBProvider(VectorDBInterface):
    def __init__(self, db_client: str, default_vector_size: int = 768,
                                     distance_method: str = None, index_threshold: int=100):
        self.client = None
        self.db_client = db_client
        self.distance_method = DistanceMethodEnums[distance_method.upper()]
        self.default_vector_size = default_vector_size
        self.index_threshold = index_threshold
        self.logger = logging.getLogger('uvicorn')

    async def connect(self):
         try:
            if self.client is None:
                self.client = QdrantClient(path=self.db_client)
                self.logger.info(f"Successfully connected to QdrantDB at {self.db_client}")
                self.client.get_collections()
                self.logger.info("Successfully retrieved collections")
         except Exception as e:
            self.logger.error(f"Error connecting to QdrantDB: {e}")
            raise e

    
    async def disconnect(self):
        self.client = None
        self.logger.info("Disconnected from QdrantDB")
        
    
    async def is_collection_existed(self, collection_name: str) -> bool:
        return self.client.collection_exists(collection_name=collection_name)

    async def list_all_collections(self) -> list:
        return self.client.get_collections()
    
    async def get_collection_info(self, collection_name: str) -> dict:
        return self.client.get_collection(collection_name)
    
    async def delete_collection(self, collection_name: str):
        if await self.is_collection_existed(collection_name):
            return self.client.delete_collection(collection_name=collection_name)
        else:
            self.logger.warning(f"Collection {collection_name} does not exist")
        
    
    async def create_collection(self, collection_name: str, 
                                embedding_size: int,
                                do_reset: bool = False):
        if do_reset:
            _ = await self.delete_collection(collection_name=collection_name)
          
        if not await self.is_collection_existed(collection_name):
            self.logger.info(f"Creating new Qdrant collection: {collection_name}")
            _ =  self.client.create_collection(
                collection_name=collection_name,
                vectors_config=models.VectorParams(
                    size=embedding_size,
                    distance=self.distance_method.value
                )   
            )
            self.logger.info(f"Collection created: {collection_name}")
            return True
        return False
    
    async def insert_one(self, collection_name: str, text: str, vector: list,
                         metadata: dict = None, record_id: str = None):
        if not self.is_collection_existed(collection_name):
            self.logger.warning(f"Collection {collection_name} does not exist")
            return False

        if record_id is None:
            import uuid
            record_id = str(uuid.uuid4())

        if metadata is None:
            metadata = {}

        try:
            _ = self.client.upsert(
                collection_name=collection_name,
                points=[
                    models.PointStruct(
                        id=record_id,
                        vector=vector,
                        payload={
                            "text": text, "metadata": metadata
                        }
                    )
                ]
            )
        except Exception as e:
            self.logger.error(f"Error while inserting record: {e}")
            return False

        return True
            
    async def insert_many(self, collection_name: str, texts: list, 
                          vectors: list, metadata: list = None, 
                          record_ids: list = None, batch_size: int = 50):
        
        if not self.is_collection_existed(collection_name):
            self.logger.warning(f"Collection {collection_name} does not exist")
            return False

        if metadata is None:
            metadata = [{}] * len(texts)

        if record_ids is None:
            import uuid
            record_ids = [str(uuid.uuid4()) for _ in texts]

        for i in range(0, len(texts), batch_size):
            batch_end = i + batch_size

            batch_texts = texts[i:batch_end]
            batch_vectors = vectors[i:batch_end]
            batch_metadata = metadata[i:batch_end]
            batch_record_ids = record_ids[i:batch_end]

            batch_records = [
                models.PointStruct(
                    id=batch_record_ids[x],
                    vector=batch_vectors[x],
                    payload={
                        "text": batch_texts[x], "metadata": batch_metadata[x]
                    }
                )
                for x in range(len(batch_texts))
            ]

            try:
                _ = self.client.upsert(
                    collection_name=collection_name,
                    points=batch_records,
                )
            except Exception as e:
                self.logger.error(f"Error while inserting batch: {e}")
                return False

        return True  
        
        
           
                                    
    async def search_by_vector(self, collection_name: str, vector: list, limit: int = 5):
        
        response = self.client.query_points(
            collection_name=collection_name,
            query=vector,
            limit=limit
        )
        return [
            RetrievedDocument(
                text=point.payload['text'],
                score=point.score
            ) for point in response.points
        ]