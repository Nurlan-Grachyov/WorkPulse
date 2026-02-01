from fastapi import FastAPI

from app.routers.user import user_router

fast_api_app = FastAPI()

fast_api_app.include_router(user_router)
