from pydantic import BaseModel, Field, validator
from typing import Optional
from bson.objectid import ObjectId

class Project(BaseModel):
    id: Optional[ObjectId] = Field(None, alias="_id")
    project_id: str = Field(..., min_length=1)

    @validator('project_id')
    def validate_project_id(cls, value):
        if not value.isalnum():
            raise ValueError('project_id must be alphanumeric')
        
        return value
    
    @classmethod
    def get_indexes(cls):
        return [
            {   "key": [("project_id", 1)],  # Index on project_id field , 1 for ascending order
                "name": "project_id_index",  # Name of the index
                "unique": True   # Ensure project_id is unique across documents 
            } 
        ]

    class Config:
        arbitrary_types_allowed = True