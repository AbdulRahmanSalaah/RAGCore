from .BaseDataModel import BaseDataModel
from .db_schemes import DataChunk
from .enums.DataBaseEnum import DataBaseEnum
from bson.objectid import ObjectId
from pymongo import InsertOne


class ChunkModel(BaseDataModel):
    def __init__(self, db_client: object):
        super().__init__(db_client)
        self.chunk_collection = db_client[DataBaseEnum.COLLECTION_CHUNK_NAME.value]

    
    async def insert_chunks(self,chunk:DataChunk):
        result = await self.chunk_collection.insert_one(chunk.dict(by_alias=True, exclude_unset=True)) 
        chunk._id = result.inserted_id  
        return chunk  
    
    
    async def get_chunks(self,chunk_id:str):
        result = await self.chunk_collection.find_one({
            "_id": ObjectId(chunk_id)
        })

        if result is None:
            return None
        
        return DataChunk(**result)
    



    async def insert_many_chunks(self, chunks: list, batch_size: int=100):

        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i+batch_size]

            operations = [
                InsertOne(chunk.dict(by_alias=True, exclude_unset=True))
                for chunk in batch
            ]

            await self.chunk_collection.bulk_write(operations)
        
        return len(chunks)

    async def delete_chunks_by_kb_id(self, kb_id: ObjectId):
        

        result = await self.chunk_collection.delete_many({
            "chunk_kb_id": kb_id
        })
        return result.deleted_count  