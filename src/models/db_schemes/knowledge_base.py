from pydantic import BaseModel, Field, validator
from typing import Optional
from bson.objectid import ObjectId

class KnowledgeBase(BaseModel):
    id: Optional[ObjectId] = Field(None, alias="_id")
    kb_id: str = Field(..., min_length=1)

    @validator('kb_id')
    def validate_kb_id(cls, value):
        if not value.isalnum():
            raise ValueError('kb_id must be alphanumeric')
        
        return value
    
    @classmethod
    def get_indexes(cls):
        return [
            {   "key": [("kb_id", 1)],  # Index on kb_id field , 1 for ascending order
                "name": "kb_id_index",  # Name of the index
                "unique": True   # Ensure kb_id is unique across documents 
            } 
        ]

    class Config:
        arbitrary_types_allowed = True