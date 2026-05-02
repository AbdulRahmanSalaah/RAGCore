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

    class Config:
        arbitrary_types_allowed = True