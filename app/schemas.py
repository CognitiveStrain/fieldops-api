from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

Priority = Literal["low", "medium", "high", "critical"]
Status = Literal["open", "in_progress", "blocked", "done"]
SortBy = Literal["id", "title", "priority", "status", "assignee", "created_at", "updated_at"]
SortOrder = Literal["asc", "desc"]
UserRole = Literal["viewer", "technician", "manager", "admin"]


class UserCreate(BaseModel):
    email: EmailStr
    full_name: str | None = Field(default=None, min_length=1, max_length=120)
    password: str = Field(min_length=8, max_length=128)


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    full_name: str | None
    role: UserRole
    is_active: bool
    created_at: datetime


class UserRoleUpdate(BaseModel):
    role: UserRole


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class WorkOrderCreate(BaseModel):
    title: str = Field(min_length=3, max_length=120)
    description: str = Field(default="", max_length=2000)
    priority: Priority = "medium"
    assignee: str | None = Field(default=None, max_length=80)


class WorkOrderUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=120)
    description: str | None = Field(default=None, max_length=2000)
    priority: Priority | None = None
    status: Status | None = None
    assignee: str | None = Field(default=None, max_length=80)


class WorkOrderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str
    priority: Priority
    status: Status
    assignee: str | None
    created_by_id: int | None
    created_at: datetime
    updated_at: datetime
