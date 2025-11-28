from pydantic import BaseModel, EmailStr, constr, conint, ValidationError, field_validator

class User(BaseModel):
    username: str
    password: str
    phone: str
    email: EmailStr
    user_type: int


    @field_validator('password')
    @classmethod
    def password_length(cls, v):
        if len(v) < 8:
            raise ValueError('password must be at least eight characters')
        return v

    @field_validator('phone')
    @classmethod
    def phone_number_format(cls, v):
        if not v.isdigit() or len(v) != 10:
            raise ValueError('phone number must be a 10-digit number')
        return v





