from .BaseController import BaseController
from .KnowledgeBaseController import KnowledgeBaseController  

import os 

from langchain_community.document_loaders import TextLoader
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from models import ProcessingEnum


class ProcessFileController(BaseController):
    def __init__(self, kb_id: str):
        super().__init__()

        self.kb_id = kb_id
        self.kb_path = KnowledgeBaseController().get_kb_path(kb_id=kb_id)
    
    def get_file_extension(self,file_id:str):
        return os.path.splitext(file_id)[-1]
    

    def get_file_loader(self,file_id:str): # loader is the way to load the file from the file system to the memory
        file_extension = self.get_file_extension(file_id)
        file_path = os.path.join(self.kb_path, file_id)

        if file_extension == ProcessingEnum.TXT.value:
            return TextLoader(file_path, encoding="utf-8")
        elif file_extension == ProcessingEnum.PDF.value:
            return PyMuPDFLoader(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_extension}")



    def get_file_content(self,file_id:str): 
        loader = self.get_file_loader(file_id)
        return loader.load()  # .load() method will return the content of the file in the form of list of Document objects


    
    def process_file_content(self,file_content:list,chunk_size:int,chunk_overlap:int):



        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,  
        )
        
        chunks = text_splitter.split_documents(documents=file_content)
           

        return chunks
        

    

    