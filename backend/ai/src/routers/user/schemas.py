from pydantic import BaseModel, Field
from typing import Optional
import datetime


class UserCreate(BaseModel):
    name: str
    phone: str
    password: str
    email: Optional[str] = None
    address: Optional[str] = None
    avatar: Optional[str] = None
    bio: Optional[str] = None


class UserUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    password: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    avatar: Optional[str] = None
    bio: Optional[str] = None
    wordNumber: Optional[int] = None
    dayNumber: Optional[int] = None
    isTimingTask: Optional[bool] = None
    timingTaskTime: Optional[str] = None


class UserRead(BaseModel):
    id: str
    name: str
    phone: str
    email: Optional[str]
    address: Optional[str]
    avatar: Optional[str]
    bio: Optional[str]
    wordNumber: int
    dayNumber: int
    isTimingTask: bool
    timingTaskTime: str
    createdAt: datetime.datetime
    updatedAt: datetime.datetime
    lastLoginAt: Optional[datetime.datetime]

    model_config = {"from_attributes": True}
