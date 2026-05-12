from .BaseDataModel import BaseDataModel
from .db_schemes import KnowledgeBase
from .enums.DataBaseEnum import DataBaseEnum


class KnowledgeBaseModel(BaseDataModel):
    def __init__(self, db_client: object):
        super().__init__(db_client)
        self.kb_collection = db_client[DataBaseEnum.COLLECTION_KNOWLEDGE_BASE_NAME.value]
        
# The create_instance class method is an asynchronous factory method that initializes an instance of the KnowledgeBaseModel class. It takes a database client as an argument, creates an instance of the class, and then calls the init_collection method to ensure that the necessary collection and indexes are set up in the database before returning the instance. This pattern is useful for performing asynchronous initialization tasks that may be required before the instance can be used effectively.
    @classmethod
    async def create_instance(cls, db_client: object):
        instance = cls(db_client)
        await instance.init_collection()
        return instance


# This method checks if the collection for knowledge bases exists in the database. If it does not exist, it creates the collection and sets up the necessary indexes based on the specifications defined in the KnowledgeBase model. This ensures that the database is properly structured to store and manage knowledge base records efficiently.
    async def init_collection(self):  # 
        all_collections = await self.db_client.list_collection_names()
        if DataBaseEnum.COLLECTION_KNOWLEDGE_BASE_NAME.value not in all_collections:
            self.kb_collection =  self.db_client[DataBaseEnum.COLLECTION_KNOWLEDGE_BASE_NAME.value]
            indexes = KnowledgeBase.get_indexes()
            for index in indexes:
                await self.kb_collection.create_index(
                    index["key"], 
                    name=index["name"], 
                    unique=index["unique"]
                )   
        

    async def insert_knowledge_base(self, kb: KnowledgeBase):
        result = await self.kb_collection.insert_one(kb.dict(by_alias=True, exclude_unset=True)) # the dict() method of a Pydantic model converts the model instance into a dictionary. 
        kb.id = result.inserted_id
        return kb
    


    async def get_knowledge_base_or_create(self,kb_id:str):
        record = await self.kb_collection.find_one({  # find_one() method will return the document if it is found, otherwise it will return None
            "kb_id": kb_id
        })

        if record is None: # if the document is not found, create it using KnowledgeBase(kb_id=kb_id) and then insert it into the collection  
            kb = KnowledgeBase(kb_id=kb_id)
            kb = await self.insert_knowledge_base(kb)
            return kb
        
        return KnowledgeBase(**record)   # **record is used to unpack the dictionary and create a KnowledgeBase object from it



    async def get_all_knowledge_bases(self,page:int = 1 ,page_size:int = 10):
        # count total number of documents
        total_documents = await self.kb_collection.count_documents({})

        # calculate total number of pages
        total_pages = total_documents // page_size
        if total_documents % page_size > 0:
            total_pages += 1

        cursor = self.kb_collection.find().skip( (page-1) * page_size ).limit(page_size)
        kbs = []
        async for document in cursor:
            kbs.append(
                KnowledgeBase(**document)
            )

        return kbs, total_pages