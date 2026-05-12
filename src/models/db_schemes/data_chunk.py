from pydantic import BaseModel, Field, validator
from typing import Optional
from bson.objectid import ObjectId

class DataChunk(BaseModel):
    id: Optional[ObjectId] = Field(None, alias="_id")
    chunk_text: str = Field(..., min_length=1)
    chunk_metadata: dict
    chunk_order: int = Field(..., gt=0)
    chunk_kb_id: ObjectId
    
    
    @classmethod
    def get_indexes(cls):
        return [
            {   "key": [("chunk_kb_id", 1)],  # Index on chunk_kb_id field , 1 for ascending order
                "name": "chunk_kb_id_index",  # Name of the index
                "unique": False   # Allow duplicate values in this index
            } 
        ]

    class Config:
        arbitrary_types_allowed = True
