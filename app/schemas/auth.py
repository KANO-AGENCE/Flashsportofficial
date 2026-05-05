from pydantic import BaseModel


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserCreate(BaseModel):
    email: str
    password: str
    first_name: str = ""
    last_name: str = ""
    role: str = "POSTE_TRI"
    modules: list[str] = ["TRI"]


class UserUpdate(BaseModel):
    email: str | None = None
    password: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    role: str | None = None
    modules: list[str] | None = None
    is_active: bool | None = None


class UserOut(BaseModel):
    id: int
    email: str
    first_name: str
    last_name: str
    role: str
    modules: list[str]
    is_active: bool

    class Config:
        from_attributes = True
