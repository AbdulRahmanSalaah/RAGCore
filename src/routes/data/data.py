from fastapi import APIRouter, Depends, UploadFile ,status, Request
from fastapi.responses import JSONResponse
from helpers.config import get_settings, Settings
from controllers import DataController ,  ProcessFileController
import aiofiles
from models import ResponseSignal  
import logging
from .schemes.data import ProcessFileRequest
from models .KnowledgeBaseModel import KnowledgeBaseModel 
from models .ChunkModel import ChunkModel
from models .db_schemes import DataChunk


data_router = APIRouter(
    prefix="/api/v1/data",
    tags=["data"],
)

@data_router.post("/upload/{kb_id}")
async def upload_file(request: Request,kb_id: str, file: UploadFile, app_settings: Settings = Depends(get_settings)):

    kb_model = await KnowledgeBaseModel.create_instance(db_client=request.app.db_client)

    kb = await kb_model.get_knowledge_base_or_create(kb_id=kb_id)

    
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
    file_path, saved_file_name = data_controller.generate_unique_filepath(kb_id, file.filename) 
    
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
            "file_name": saved_file_name,
            "kb_id": str(kb.id)
        }
    )
        
        

        

    



@data_router.post("/process/{kb_id}")
async def process_file(request:Request,kb_id: str, process_request: ProcessFileRequest):
    file_id = process_request.file_id
    chunk_size = process_request.chunk_size
    chunk_overlap = process_request.chunk_overlap
    do_reset = process_request.do_reset
    
    
    kb_model = await KnowledgeBaseModel.create_instance(db_client=request.app.db_client)

    kb = await kb_model.get_knowledge_base_or_create(kb_id=kb_id)

    process_file_controller = ProcessFileController(kb_id=kb_id)

    file_content = process_file_controller.get_file_content(file_id=file_id)
    file_chunks = process_file_controller.process_file_content(file_content=file_content,chunk_size=chunk_size,chunk_overlap=chunk_overlap)

    if file_chunks is None or len(file_chunks) == 0:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "signal": ResponseSignal.FILE_PROCESSING_FAILED.value
            }
        )

    
    chunks_model = await ChunkModel.create_instance(db_client=request.app.db_client)


        
        
    file_chunks_records = [
            DataChunk(
                chunk_kb_id = kb.id,   
                chunk_order = i+1,
                chunk_text = chunk.page_content,
                chunk_metadata = {
                    "source": chunk.metadata.get("source"),
                    "title" : chunk.metadata.get("title"), 
                    "kb_id": str(kb.id),
                    "page": chunk.metadata.get("page"),
                    "author": chunk.metadata.get("author"),
                    "keywords": chunk.metadata.get("keywords"),
                    "total_pages": chunk.metadata.get("total_pages")
                },
            )
            for i, chunk in enumerate(file_chunks)
    ]
    
    
    if do_reset == 1:
        _ = await chunks_model.delete_chunks_by_kb_id(
            kb_id=kb.id
        )    
    
    number_of_records = await chunks_model.insert_many_chunks(chunks=file_chunks_records)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "signal": ResponseSignal.FILE_PROCESSING_SUCCESS.value,
            "number_of_records": number_of_records
        }
    )
    
    
    

    


    


    
    
   
    
    
