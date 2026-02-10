from pydantic import BaseModel , Field , EmailStr
from datetime import datetime 
from enum import Enum
class SummaryType(str , Enum):
    static = 'static'
    deep = 'deep'


class SummaryModel(BaseModel):
    user_id : int = Field(...)
    summary_type : SummaryType = Field(...)
    filename: str = Field(... , min_length=3)
    max_length : int = Field(...)
    
