from pydantic import BaseModel , Field , EmailStr
from datetime import datetime 
from enum import Enum

class UserSignUpModel(BaseModel):
    name: str = Field(..., min_length=3, max_length=20)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=20)

class UserLoginModel(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=20)




