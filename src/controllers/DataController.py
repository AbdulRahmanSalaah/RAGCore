from .BaseController import BaseController 
from .KnowledgeBaseController import KnowledgeBaseController
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

    
    def generate_unique_filepath(self, kb_id: str, orig_file_name: str):
        
        random_str = self.generate_random_string()
         
        kb_path = KnowledgeBaseController().get_kb_path(kb_id) #  make a folder for each knowledge_base and add it to the files directory
         
        cleaned_file_name = self.get_clean_file_name(orig_file_name) # clean the file name


        new_file_name = os.path.join( # create a new file name with a random string and the cleaned file name
            kb_path, 
             random_str + "_" + cleaned_file_name
        )
        
        while os.path.exists(new_file_name): # check if the file already exists, if it does, create a new random string and try again
            random_str = self.generate_random_string()
            new_file_name = os.path.join(
                kb_path, 
                random_str + "_" + cleaned_file_name
            )

        return new_file_name, random_str + "_" + cleaned_file_name  # return the new file name and the new file name without the path
