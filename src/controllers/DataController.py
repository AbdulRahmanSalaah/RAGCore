from .BaseController import BaseController 
from .ProjectController import ProjectController
from fastapi import UploadFile
from models import ResponseSignal
import os
import re



class DataController(BaseController):
    
    def __init__(self):
        super().__init__()
        self.size_scale = 1048576 # convert MB to bytes

    def validate_uploaded_file(self, file: UploadFile):
        
        if file.content_type not in self.app_settings.FILE_ALLOWED_TYPES:
            return False, ResponseSignal.FILE_TYPE_NOT_SUPPORTED.value

        if file.size is not None and file.size > self.app_settings.FILE_MAX_SIZE * self.size_scale:
            return False, ResponseSignal.FILE_SIZE_EXCEEDED.value
        

        return True, ResponseSignal.FILE_VALIDATED_SUCCESS.value
    
    
    def get_clean_file_name(self, orig_file_name: str):

        # remove any special characters, except underscore and .
        cleaned_file_name = re.sub(r'[^\w.]', '', orig_file_name.strip())

        # replace spaces with underscore
        cleaned_file_name = cleaned_file_name.replace(" ", "_")

        return cleaned_file_name

    
    def generate_unique_file_name(self, project_id: str, orig_file_name: str):
        
        random_str = self.generate_random_string()
         
        projet_path = ProjectController().get_project_path(project_id)
         
        cleaned_file_name = self.get_clean_file_name(orig_file_name)


        new_file_name = os.path.join(
            projet_path, 
             random_str + "_" + cleaned_file_name
        )
        
        while os.path.exists(new_file_name):
            random_str = self.generate_random_string()
            new_file_name = os.path.join(
                projet_path, 
                random_str + "_" + cleaned_file_name
            )

        return new_file_name, random_str + "_" + cleaned_file_name

