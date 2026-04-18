from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

class UserCreate(BaseModel):
    email: str

class UserResponse(BaseModel):
    id: int
    email: str
    created_at: datetime
    class Config:
        from_attributes = True

class SwingResponse(BaseModel):
    id: int
    user_id: int
    video_path: str
    created_at: datetime
    class Config:
        from_attributes = True

class PoseResponse(BaseModel):
    frame_index: int
    keypoints_json: str
    class Config:
        from_attributes = True

class AnalysisResponse(BaseModel):
    result_json: str
    class Config:
        from_attributes = True

class LessonResponse(BaseModel):
    lesson_text: str
    class Config:
        from_attributes = True
