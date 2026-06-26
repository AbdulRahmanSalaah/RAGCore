from pydantic import BaseModel, Field, validator
from typing import Optional
from bson.objectid import ObjectId
from datetime import datetime

class Asset(BaseModel):
    id: Optional[ObjectId] = Field(None, alias="_id")
    asset_project_id: ObjectId
    asset_type: str = Field(..., min_length=1)

    asset_name: str = Field(..., min_length=1)
    asset_size: int = Field(ge=0, default=None) 
    asset_metadata: dict = Field(default=None)
    asset_pushed_at: datetime = Field(default=datetime.utcnow)
    
    
    
    @classmethod
    def get_indexes(cls):
        return [
            {   "key": [("asset_project_id", 1)],  # Index on asset_project_id field , 1 for ascending order
                "name": "asset_project_id_index",  # Name of the index
                "unique": False   # Allow duplicate values in this index
            } ,
            {
                "key": [("asset_project_id", 1),
                        ("asset_name", 1)
                    ],  # Index on asset_name field , 1 for ascending order
                "name": "asset_project_id_name_index",  # Name of the index
                "unique": False   # Allow duplicate values in this index
            }
            
        ]

    class Config:
        arbitrary_types_allowed = True