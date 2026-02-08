from pydantic import BaseModel, ConfigDict


class TeamCreate(BaseModel):
    title: str

    class Config:
        json_schema_extra = {
            "example": {
                "title": "Create an employer's system",
            }
        }


class TeamGet(BaseModel):
    id: int
    slug: str
    title: str

    model_config = ConfigDict(from_attributes=True)
