from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

Priority = Literal["low", "medium", "high", "critical"]
Status = Literal["open", "in_progress", "blocked", "done"]


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
    created_at: datetime
