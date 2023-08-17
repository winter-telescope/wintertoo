"""
Base model for the program database

Duplicated (sorry) from mirar/pipelines/summer/models/program.py, to avoid
an elaborate web of imports for WSP.
"""
from datetime import date
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, FieldValidationInfo, field_validator


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
    hours_allocated: float = Field(ge=0.0, default=None)
    hours_remaining: float = Field(ge=0.0, default=None)
    maxpriority: float = Field(description="Max priority")
    progtitle: str = Field(min_length=1, example="A program title", default=None)

    @field_validator("enddate")
    @classmethod
    def check_date(cls, enddate: date, info: FieldValidationInfo) -> date:
        """
        Ensure dates are correctly formatted

        :param enddate: end date
        :param info: field validation info
        :return: end date
        """
        startdate = info.data["startdate"]
        assert enddate > startdate
        return enddate

    @field_validator("hours_remaining")
    @classmethod
    def validate_time_allocation(
        cls, hours_remaining: float, info: FieldValidationInfo
    ) -> float:
        """
        Ensure that time remaining has a sensible value

        :param hours_remaining: hours remaining
        :param info: field validation info
        :return: field value
        """
        total_time = info.data["hours_allocated"]
        assert not hours_remaining > total_time
        assert not hours_remaining < 0.0
        return hours_remaining

    model_config = ConfigDict(extra="forbid")
