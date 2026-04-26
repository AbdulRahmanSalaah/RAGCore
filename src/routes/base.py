from fastapi import FastAPI, APIRouter, Depends
import os
from helpers.config import get_settings, Settings

base_router = APIRouter( 
    prefix="/api/v1",  #  prefix is the same for all routers in the folder 
    tags=["api_v1"],  #  tags defind in the router
)

@base_router.get("/")
async def welcome(app_settings: Settings = Depends(get_settings)):
    app_name = app_settings.APP_NAME
    app_version = app_settings.APP_VERSION
  

    return {
        "app_name": app_name,
        "app_version": app_version,
    }