import os

from fastapi import APIRouter, Depends, UploadFile ,status, Request
from fastapi.responses import JSONResponse
from helpers.config import get_settings, Settings
from controllers import DataController ,  ProcessFileController
import aiofiles
from models import AssetTypeEnum, ResponseSignalEnum 
import logging


from .schemes.data import ProcessFileRequest
from models .ProjectModel import ProjectModel 
from models .ChunkModel import ChunkModel
from models .db_schemes import DataChunk , Asset

from models .AssetModel import AssetModel


data_router = APIRouter(
    prefix="/api/v1/data",
    tags=["data"],
)

@data_router.post("/upload/{project_id}")
async def upload_file(request: Request,project_id: str, file: UploadFile, app_settings: Settings = Depends(get_settings)):

    project_model = await ProjectModel.create_instance(db_client=request.app.db_client)

    project = await project_model.get_project_or_create(project_id=project_id)

    
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
    # file_path : absolute path to the file  ex : e:/kolya/mini_rag_course/project/mini_rag/src/assets/files/f266_my_document.docx
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
                "signal": ResponseSignalEnum.FILE_UPLOAD_FAILED.value
            }
        ) 
        
        # store the assets into the database
    asset_model = await AssetModel.create_instance(
        db_client=request.app.db_client
    )
    
    asset_resource =   Asset(
        asset_project_id = project.id,
        asset_type=AssetTypeEnum.FILE.value,
        asset_name = saved_file_name,
        asset_size=os.path.getsize(file_path)
    )
    
    
    asset_record = await asset_model.insert_asset(asset=asset_resource)

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "signal": ResponseSignalEnum.FILE_UPLOAD_SUCCESS.value,
            "file_name": saved_file_name,
            "asset_id": str(asset_record.id),
            "project_id": str(project.id)
        }
    )
        
        

        

    



@data_router.post("/process/{project_id}")
async def process_file(request:Request,project_id: str, process_request: ProcessFileRequest):
    # file_name = process_request.file_name
    chunk_size = process_request.chunk_size
    chunk_overlap = process_request.chunk_overlap
    do_reset = process_request.do_reset
    
    
    project_model = await ProjectModel.create_instance(db_client=request.app.db_client)

    project = await project_model.get_project_or_create(project_id=project_id)
    
    
    asset_model = await AssetModel.create_instance(
            db_client=request.app.db_client
    )
    
    
    project_files_names={} # dict of file names with key as file name and value as asset record
    if process_request.file_name:   
        asset_record = await asset_model.get_asset(
            asset_project_id=project.id, 
            asset_name=process_request.file_name
        )
        if asset_record is None:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "signal": ResponseSignalEnum.FILE_NAME_ERROR.value
                }
            )
        
        project_files_names ={
            asset_record.id: asset_record.asset_name
            
        }
    else:
        # get all the files of the project and store it in the dict with key as asset id and value as file name
        asset_records = await asset_model.get_all_project_assets(
            asset_project_id=project.id,
            asset_type=AssetTypeEnum.FILE.value
        )
        
        project_files_names = {
            asset_record.id: asset_record.asset_name
            for asset_record in asset_records
        }
        
    
    if len(project_files_names) == 0:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "signal": ResponseSignalEnum.NO_FILES_ERROR.value
            }
        )

    process_file_controller = ProcessFileController(project_id=project_id)
    
    number_of_records = 0
    no_files = 0
    
    
    chunks_model = await ChunkModel.create_instance(db_client=request.app.db_client)
    
    if do_reset == 1:
        _ = await chunks_model.delete_chunks_by_project_id(
            project_id=project.id
        ) 
    for asset_id, file_name in project_files_names.items():
        file_content = process_file_controller.get_file_content(file_name=file_name)
        if file_content is None:
            logging.error(f"Error loading file content for file: {file_name}")
            continue

        file_chunks = process_file_controller.process_file_content(
            file_content=file_content,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )

        if file_chunks is None or len(file_chunks) == 0:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "signal": ResponseSignalEnum.FILE_PROCESSING_FAILED.value
                }
            )

        
            
        file_chunks_records = [
                DataChunk(
                    chunk_project_id = project.id,   
                    chunk_asset_id = asset_id,
                    chunk_order = i+1,
                    chunk_text = chunk.page_content,
                    chunk_metadata = {
                        "source": chunk.metadata.get("source"),
                        "title" : chunk.metadata.get("title"), 
                        "project_id": str(project.id),
                        "page": chunk.metadata.get("page"),
                        "author": chunk.metadata.get("author"),
                        "keywords": chunk.metadata.get("keywords"),
                        "total_pages": chunk.metadata.get("total_pages")
                    },
                )
                for i, chunk in enumerate(file_chunks)
        ]
        
        
    
        
        number_of_records += await chunks_model.insert_many_chunks(chunks=file_chunks_records)
        no_files += 1
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "signal": ResponseSignalEnum.FILE_PROCESSING_SUCCESS.value,
            "number_of_records": number_of_records,
            "number_of_files": no_files
        }
    )
