from pydantic import BaseModel, ConfigDict


class Model(BaseModel):
    model_config = ConfigDict(validate_assignment=True, extra="allow")
