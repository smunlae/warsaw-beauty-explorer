from backend.app.api import salons, scraper
from fastapi import APIRouter

api_router = APIRouter()
api_router.include_router(salons.router, prefix="/salons", tags=["salons"])
api_router.include_router(scraper.router, prefix="/scraper", tags=["scraper"])
