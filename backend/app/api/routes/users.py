from fastapi import APIRouter, HTTPException

from app.portfolio.service import enrich_portfolio
from app.users.service import user_service

router = APIRouter()


@router.get("/api/users")
async def list_users():
    return {"users": user_service.list_users()}


@router.get("/api/users/{user_id}")
async def get_user(user_id: str):
    user = user_service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail=f"User '{user_id}' not found")
    return user


@router.get("/api/users/{user_id}/portfolio")
async def get_user_portfolio(user_id: str):
    user = user_service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail=f"User '{user_id}' not found")
    return enrich_portfolio(user.get("portfolio", {}))