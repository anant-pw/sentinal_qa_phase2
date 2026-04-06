from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime # Fixes the AttributeError

class StepSchema(BaseModel):
    action: str
    selector: Optional[str] = None
    data: Optional[str] = None
    sequence: Optional[int] = 0

    class Config:
        from_attributes = True

class PlanCreate(BaseModel):
    title: str
    steps: List[StepSchema]

class StepsUpdate(BaseModel):
    steps: List[StepSchema]

class PlanRead(BaseModel):
    id: int
    title: str
    status: str
    steps: List[StepSchema]

    class Config:
        from_attributes = True

class ResultCreate(BaseModel):
    plan_id: int
    status: str
    failing_selector: Optional[str] = None
    error_message: Optional[str] = None
    screenshot_path: Optional[str] = None

class ResultRead(ResultCreate):
    id: int
    created_at: datetime # Use the imported class directly

    class Config:
        from_attributes = True