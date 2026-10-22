from pydantic import BaseModel, ConfigDict


class ORMModel(BaseModel):
    """Base for all schemas: read from ORM objects and use plain strings for enums."""

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)
