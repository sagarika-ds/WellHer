from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

Score5 = Annotated[int, Field(ge=1, le=5)]


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class Ok(BaseModel):
    ok: bool = True
