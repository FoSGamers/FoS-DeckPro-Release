# Version History: 0.7.2 -> 0.7.3
from fastapi import APIRouter, HTTPException
from app.core.config import logger

router = APIRouter()

@router.get("/auth/login/{platform}")
async def login_platform(platform: str):
    logger.info(f"Login requested for platform: {platform}")
    raise HTTPException(status_code=501, detail="Not implemented")

