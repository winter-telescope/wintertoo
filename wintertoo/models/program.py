"""
Base model for the program database

Duplicated (sorry) from mirar/pipelines/summer/models/program.py, to avoid
an elaborate web of imports for WSP.
"""

from datetime import date
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ProgramCredentials(BaseModel):
    """
    Program credentials to access a program
    """

    progname: str = Field(min_length=8, max_length=8, example="2020A000")
    prog_key: str = Field()


class Program(ProgramCredentials):
    """
    A pydantic model for a program database entry
    """

    puid: Optional[int] = Field(default=None)
    progid: int = Field(default=1)
    pi_name: str = Field(min_length=1, example="Hubble", default=None)
    pi_email: str = Field(min_length=1, example="someone@institute.com", default=None)
    startdate: date = Field()
    enddate: date = Field()
    hours_allocated: float = Field(ge=0.0, default=0.0)
    hours_used: float = Field(ge=0.0, default=0.0)
    maxpriority: float = Field(description="Max priority")
    progtitle: str = Field(min_length=1, example="A program title", default=None)

    @model_validator(mode="after")
    def check_date(self):
        """
        Ensure dates are correctly formatted

        :return: self
        """
        startdate = self.startdate
        enddate = self.enddate
        assert enddate > startdate
        return self

    @model_validator(mode="after")
    def validate_time_allocation(self):
        """
        Ensure that time remaining has a sensible value

        :return: self
        """
        total_time = self.hours_allocated
        hours_used = self.hours_used
        assert hours_used <= total_time
        assert hours_used >= 0.0
        return self

    model_config = ConfigDict(extra="forbid")
