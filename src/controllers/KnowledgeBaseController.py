from .BaseController import BaseController
from fastapi import UploadFile
from models import ResponseSignal
import os

class KnowledgeBaseController(BaseController):
    
    def __init__(self):
        super().__init__()
        
    def get_kb_path(self, kb_id: str):
        kb_dir  = os.path.join(    # this line to make folder with name kb_id
            self.files_dir, 
            kb_id
        )  
         
        if not os.path.exists(kb_dir):    # this line to check if the folder exists and  create it if not
            os.makedirs(kb_dir)
            
            
        return kb_dir