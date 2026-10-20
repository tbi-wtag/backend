import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator

class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    first_name: str = Field(...,min_length = 2,  max_length = 50)
    last_name: str = Field(..., min_length=2, max_length=50)
    email: EmailStr = Field(..., max_length=100)

class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=255)
    confirm_password: str = Field(..., min_length=8, max_length=255)

    @model_validator(mode="after")
    def verify_password_match(self) -> "UserCreate":
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match")
        return self

class UserUpdate(BaseModel):
    username: str | None = Field(None, min_length=3, max_length=50)
    first_name: str | None = Field(None, min_length=2, max_length=50)
    last_name: str | None = Field(None, min_length=2, max_length=50)
    email: EmailStr | None = Field(None, max_length=100)

class UserPasswordUpdate(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=8, max_length=255)
    confirm_new_password: str = Field(...,min_length=8, max_length=255)

    @model_validator(mode="after")
    def verify_new_password_match(self) -> "UserPasswordUpdate":
        if self.new_password != self.confirm_new_password:
            raise ValueError("Passwords do not match")
        return self

class UserResponse(UserBase):
    id: uuid.UUID
    role: str
    created_at: datetime
    updated_at: datetime


    model_config = ConfigDict(from_attributes=True)