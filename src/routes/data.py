from fastapi import APIRouter, Depends, UploadFile ,status
from fastapi.responses import JSONResponse
from helpers.config import get_settings, Settings
from controllers import DataController , ProcessController
import aiofiles
from models import ResponseSignal
import logging
from .schemes.data import ProcessFileRequest


data_router = APIRouter(
    prefix="/api/v1/data",
    tags=["data"],
)

@data_router.post("/upload/{project_id}")
async def upload_file(project_id: str, file: UploadFile, app_settings: Settings = Depends(get_settings)):
    # validate the file properties
    data_controller = DataController()
    is_valid, message = data_controller.validate_uploaded_file(file)

    if not is_valid:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "signal": message  
            }
        )
    # file_path : absolute path to the file
    # saved_file_name : file name with random string and cleaned file name
    file_path, saved_file_name = data_controller.generate_unique_filepath(project_id, file.filename) 
    
    try:
        # save the file to the file system using aiofiles and chunk size from app_settings 
        # in binary mode write mode (wb)  
        async with aiofiles.open(file_path, "wb") as f:
            while chunk := await file.read(app_settings.FILE_DEFAULT_CHUNK_SIZE):
                await f.write(chunk)
    except Exception as e:      
        logging.error(f"Error saving file: {e}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "signal": ResponseSignal.FILE_UPLOAD_FAILED.value
            }
        ) 

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "signal": ResponseSignal.FILE_UPLOAD_SUCCESS.value,
            "file_name": saved_file_name
        }
    )
        
        

        

    



@data_router.post("/process/{project_id}")
async def process_endpoint(project_id: str, process_request: ProcessFileRequest):
    file_id = process_request.file_id
    chunk_size = process_request.chunk_size
    chunk_overlap = process_request.chunk_overlap
    do_reset = process_request.do_reset

    process_controller = ProcessController(project_id=project_id)

    file_content = process_controller.get_file_content(file_id=file_id)
    file_chunks = process_controller.process_file_content(file_content=file_content,chunk_size=chunk_size,chunk_overlap=chunk_overlap)

    if file_chunks is None or len(file_chunks) == 0:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "signal": ResponseSignal.FILE_PROCESSING_FAILED.value
            }
        )

    return file_chunks

    


    
    
   
    
    
