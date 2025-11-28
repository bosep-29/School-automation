from pydantic import BaseModel

class Client(BaseModel):
    name: str
    address: str
    pricing_tier: str = "premium"