from .BaseController import BaseController
from fastapi import UploadFile
from models import ResponseSignalEnum
import os

class ProjectController(BaseController):
    
    def __init__(self):
        super().__init__()
        
    def get_project_path(self, project_id: str):
        project_dir  = os.path.join(    # this line to make folder with name project_id
            self.files_dir, 
            project_id
        )  
         
        if not os.path.exists(project_dir):    # this line to check if the folder exists and  create it if not
            os.makedirs(project_dir)
            
            
        return project_dir