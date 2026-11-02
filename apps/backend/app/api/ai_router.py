from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_current_user
from app.schemas.ai_schema import GenerateTaskIn, GenerateTaskOut
from app.services.ai_service import ai_service

router = APIRouter()


@router.post("/generate-task", response_model=GenerateTaskOut)
async def generate_task(payload: GenerateTaskIn, _user=Depends(get_current_user)):
    try:
        result = await ai_service.generate_task(payload.title)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return result
