from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional
import re

class UserCreate(BaseModel):
    name: str = Field(..., min_length=3, max_length=50, pattern="^[A-Za-z ]+$")
    email: EmailStr  
    password: str = Field(..., min_length=6, max_length=100)  
    latitude: Optional[float] = None 
    longitude: Optional[float] = None 
   


    @classmethod
    def validate_name(cls, name):
        if not re.match(r"^[A-Za-z ]+$", name):
            raise ValueError("Name must contain only letters and spaces")
        return name
    
class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    created_at: datetime
    latitude : Optional[float] = None
    longitude: Optional[float] = None

    class Config:
        orm_mode = True


class MalariaReportCreate(BaseModel):
    latitude: float
    longitude: float
    cases_reported: int

class MalariaRiskResponse(BaseModel):
    risk_level: str
    color: str


