from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from typing import List, Optional
import uuid
import datetime

from src.models.models import User
from .schemas import UserCreate, UserUpdate


class UserService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, user_data: UserCreate) -> User:
        """创建用户"""
        # 检查手机号是否已存在
        existing = await self.session.exec(select(User).where(User.phone == user_data.phone))
        if existing.first():
            raise ValueError("手机号已存在")
        
        # 检查邮箱是否已存在
        if user_data.email:
            existing = await self.session.exec(select(User).where(User.email == user_data.email))
            if existing.first():
                raise ValueError("邮箱已存在")
        
        now = datetime.datetime.now()
        user = User(
            id=str(uuid.uuid4()),
            name=user_data.name,
            phone=user_data.phone,
            password=user_data.password,
            email=user_data.email,
            address=user_data.address,
            avatar=user_data.avatar,
            bio=user_data.bio,
            wordNumber=0,
            dayNumber=0,
            isTimingTask=False,
            timingTaskTime="00:00:00",
            createdAt=now,
            updatedAt=now
        )
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def get_list(self, skip: int = 0, limit: int = 100) -> List[User]:
        """获取用户列表"""
        result = await self.session.exec(select(User).offset(skip).limit(limit))
        return list(result.all())

    async def get_by_id(self, user_id: str) -> Optional[User]:
        """根据ID获取用户"""
        return await self.session.get(User, user_id)

    async def update(self, user_id: str, user_data: UserUpdate) -> User:
        """更新用户"""
        user = await self.get_by_id(user_id)
        if not user:
            raise ValueError("用户不存在")
        
        # 检查手机号是否已被其他用户使用
        if user_data.phone and user_data.phone != user.phone:
            existing = await self.session.exec(select(User).where(User.phone == user_data.phone))
            if existing.first():
                raise ValueError("手机号已存在")
        
        # 检查邮箱是否已被其他用户使用
        if user_data.email and user_data.email != user.email:
            existing = await self.session.exec(select(User).where(User.email == user_data.email))
            if existing.first():
                raise ValueError("邮箱已存在")
        
        update_data = user_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(user, key, value)
        
        user.updatedAt = datetime.datetime.now()
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def delete(self, user_id: str) -> None:
        """删除用户"""
        user = await self.get_by_id(user_id)
        if not user:
            raise ValueError("用户不存在")
        
        await self.session.delete(user)
        await self.session.commit()
