from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints

SlugStr = Annotated[str, StringConstraints(pattern=r"^[a-z][a-z0-9_-]*$")]
"""A unique identifier string. Must follow the pattern `^[a-z][a-z0-9_-]*$`"""


class Model(BaseModel):
    model_config = ConfigDict(validate_assignment=True, extra="allow")
