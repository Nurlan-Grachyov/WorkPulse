from pydantic import BaseModel


class TeamCreate(BaseModel):
    title: str

    class Config:
        json_schema_extra = {
            "example": {
                "title": "Create employer's system",
            }
        }


class TeamGet(BaseModel):
    id: int
    title: str
