from enum import Enum


class UserRole(str, Enum):
    USER = "user"

    TRAINER_FOOTBALL = "trainer_football"
    TRAINER_BADMINTON = "trainer_badminton"
    TRAINER_TENNIS = "trainer_tennis"
    TRAINER_VOLLEYBALL = "trainer_volleyball"
    TRAINER_SWIMMING = "trainer_swimming"

    ADMIN = "admin"


class SportType(str, Enum):
    FOOTBALL = "football"
    BADMINTON = "badminton"
    TENNIS = "tennis"
    VOLLEYBALL = "volleyball"
    SWIMMING = "swimming"
