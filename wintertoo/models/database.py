"""
Model for Database Connection configurations
"""

from pydantic import BaseModel, Field


class DatabaseConfig(BaseModel):
    """
    Database connection configuration
    """

    db_user: str | None = Field(default=None)
    db_password: str | None = Field(default=None)
    db_host: str = Field(default="localhost")
    db_port: int = Field(default=5432)
    db_name: str = Field(default="summer")
