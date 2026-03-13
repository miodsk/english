from fastapi import APIRouter, HTTPException, status, Depends
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import List

from src.db.main import get_session
from .schemas import UserCreate, UserUpdate, UserRead
from .service import UserService

user_router = APIRouter()


def get_user_service(session: AsyncSession = Depends(get_session)) -> UserService:
    return UserService(session)

@user_router.post("/", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_user(user_data: UserCreate, service: UserService = Depends(get_user_service)):
    """创建用户"""
    try:
        return await service.create(user_data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@user_router.get("/", response_model=List[UserRead])
async def get_users(skip: int = 0, limit: int = 100, service: UserService = Depends(get_user_service)):
    """获取用户列表"""
    return await service.get_list(skip, limit)


@user_router.get("/{user_id}", response_model=UserRead)
async def get_user(user_id: str, service: UserService = Depends(get_user_service)):
    """获取单个用户"""
    user = await service.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
    return user


@user_router.patch("/{user_id}", response_model=UserRead)
async def update_user(user_id: str, user_data: UserUpdate, service: UserService = Depends(get_user_service)):
    """更新用户"""
    try:
        return await service.update(user_id, user_data)
    except ValueError as e:
        if "不存在" in str(e):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@user_router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: str, service: UserService = Depends(get_user_service)):
    """删除用户"""
    try:
        await service.delete(user_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
