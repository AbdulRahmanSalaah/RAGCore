from fastapi import APIRouter, status, Request
from fastapi.responses import JSONResponse
from .schemes import PushRequest, SearchRequest
from models.ProjectModel import ProjectModel
from models.ChunkModel import ChunkModel
from models import ResponseSignalEnum
from helpers.config import get_settings
from stores.llm.LLMProviderFactory import LLMProviderFactory
from controllers.NLPController import NLPController
from tqdm.auto import tqdm

nlp_router = APIRouter(
    prefix="/api/v1/nlp",
    tags=["api_v1", "nlp"],
)

@nlp_router.post("/index/push/{project_id}")
async def index_project(request: Request, project_id: int, push_request: PushRequest):
    project_model = await ProjectModel.create_instance(
        db_client=request.app.db_client
    )
    
    chunk_model = await ChunkModel.create_instance(
        db_client=request.app.db_client
    )

    project = await project_model.get_project_or_create(
        project_id=project_id,
    )
    

        
    nlp_controller = NLPController(
        vectordb_client=request.app.vector_db_client,
        generation_client=request.app.generation_client,
        embedding_client=request.app.embedding_client,
        project_id=project_id,
        template_parser=request.app.template_parser,
      )   
    
    
    has_records = True
    page_no = 1
    inserted_items_count = 0
    
    _ = await request.app.vector_db_client.create_collection(
        collection_name=nlp_controller.collection_name,
        embedding_size=request.app.embedding_client.embedding_size,
        do_reset=push_request.do_reset,
    )
    
    
    total_chunks_count = await chunk_model.get_total_chunks_count(project_id=project.id)
    pbar = tqdm(total=total_chunks_count, desc="Vector Indexing", position=0)
    
    while has_records:
        page_chunks = await chunk_model.get_project_chunks(project_id=project.id, page_no=page_no)
        if len(page_chunks):
            page_no += 1
        
        if not page_chunks or len(page_chunks) == 0:
            has_records = False
            break

        is_inserted = await nlp_controller.index_into_vector_db(
            chunks=page_chunks,
        )


        if not is_inserted:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "signal": ResponseSignalEnum.INSERT_INTO_VECTORDB_ERROR.value
                }
            )
        
        inserted_items_count += len(page_chunks)
        pbar.update(len(page_chunks))

    pbar.close()
    return JSONResponse(
        content={
            "signal": ResponseSignalEnum.INSERT_INTO_VECTORDB_SUCCESS.value,
            "inserted_items_count": inserted_items_count
        }
    )
    
    
@nlp_router.get("/index/info/{project_id}")
async def get_project_index_info(request: Request, project_id: int):
    
    project_model = await ProjectModel.create_instance(
        db_client=request.app.db_client
    )
    
    project = await project_model.get_project_or_create(
        project_id=project_id
    )

    nlp_controller = NLPController(
        project_id=project_id,
        vectordb_client=request.app.vector_db_client,
        generation_client=request.app.generation_client,
        embedding_client=request.app.embedding_client,
        template_parser=request.app.template_parser,
    )
    
    vector_db_collection_info = await nlp_controller.get_vector_db_collection_info()
    
    
    return JSONResponse(
        content={
            "signal": ResponseSignalEnum.VECTORDB_COLLECTION_RETRIEVED.value,
            "collection_info": vector_db_collection_info
        }
    )
    
    
@nlp_router.post("/index/search/{project_id}")
async def search_index(request: Request, project_id: int, search_request: SearchRequest):
    project_model = await ProjectModel.create_instance(
        db_client=request.app.db_client
    )
    
    project = await project_model.get_project_or_create(
        project_id=project_id
    )

    nlp_controller = NLPController(
        project_id=project_id,
        vectordb_client=request.app.vector_db_client,
        generation_client=request.app.generation_client,
        embedding_client=request.app.embedding_client,
        template_parser=request.app.template_parser,
    )
    
    results = await nlp_controller.search_vector_db_collection(
        text=search_request.text,
        limit=search_request.limit
    )

    if not results:
        return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "signal": ResponseSignalEnum.VECTORDB_SEARCH_ERROR.value
                }
            )
    
    return JSONResponse(
        content={
            "signal": ResponseSignalEnum.VECTORDB_SEARCH_SUCCESS.value,
            "results": [ result.dict()  for result in results ]
        }
    )
    
    
    
    
    
@nlp_router.post("/index/answer/{project_id}")
async def answer_rag(request: Request, project_id: int, search_request: SearchRequest):
    
    project_model = await ProjectModel.create_instance(
        db_client=request.app.db_client
    )
    
    project = await project_model.get_project_or_create(
        project_id=project_id
    )

    nlp_controller = NLPController(
        project_id=project_id,
        vectordb_client=request.app.vector_db_client,
        generation_client=request.app.generation_client,
        embedding_client=request.app.embedding_client,
        template_parser=request.app.template_parser,
    )
    
    answer, full_prompt, chat_history = await nlp_controller.answer_rag_question(
        query=search_request.text,
        limit=search_request.limit
    )
    
    if not answer:
        return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "signal": ResponseSignalEnum.RAG_ANSWER_ERROR.value
                }
        )
    
    return JSONResponse(
        content={
            "signal": ResponseSignalEnum.RAG_ANSWER_SUCCESS.value,
            "answer": answer,
            "full_prompt": full_prompt,
            "chat_history": chat_history
        }
    )
    