from enum import Enum
from pydantic import BaseModel


class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"


class UserBase(BaseModel):
    role: UserRole = UserRole.USER


class SportType(str, Enum):
    FOOTBALL = "football"
    BADMINTON = "badminton"
    TENNIS = "tennis"
    VOLLEYBALL = "volleyball"
    SWIMMING = "swimming"
