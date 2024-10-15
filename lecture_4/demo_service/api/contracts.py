from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, SecretStr, field_serializer

from lecture_4.demo_service.core.users import UserEntity, UserRole


class RegisterUserRequest(BaseModel):
    username: str
    name: str
    birthdate: datetime
    password: SecretStr

    @field_serializer('password', when_used='json')
    def dump_secret(self, v):
        return v.get_secret_value()
    
    @field_serializer('birthdate', when_used='json')
    def dump_date(self, v):
        return v.isoformat()


class UserResponse(BaseModel):
    uid: int
    username: str
    name: str
    birthdate: datetime
    role: UserRole

    @staticmethod
    def from_user_entity(entity: UserEntity) -> UserResponse:
        return UserResponse(
            uid=entity.uid,
            **entity.info.model_dump(exclude={"password"}),
        )


class UserAuthRequest(BaseModel):
    username: str
    password: SecretStr
