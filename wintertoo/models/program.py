"""
Base model for the program database

Duplicated (sorry) from mirar/pipelines/summer/models/program.py, to avoid
an elaborate web of imports for WSP.
"""
from datetime import date

from pydantic import BaseModel, Extra, Field, validator


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

    puid: int = Field(default=None)
    progid: int = Field(default=1)
    pi_name: str = Field(min_length=1, example="Hubble", default=None)
    pi_email: str = Field(min_length=1, example="someone@institute.com", default=None)
    startdate: date = Field()
    enddate: date = Field()
    hours_allocated: float = Field(ge=0.0, default=None)
    hours_remaining: float = Field(ge=0.0, default=None)
    maxpriority: float = Field(description="Max priority")
    progtitle: str = Field(min_length=1, example="A program title", default=None)

    @validator("enddate")
    @classmethod
    def check_date(cls, field_value, values):
        """
        Ensure dates are correctly formatted

        """
        startdate = values["startdate"]
        assert field_value > startdate
        return field_value

    @validator("hours_remaining")
    @classmethod
    def validate_time_allocation(cls, field_value, values):
        """
        Ensure that time remaining has a sensible value

        :param field_value: field value
        :param values: values
        :return: field value
        """
        total_time = values["hours_allocated"]
        assert not field_value > total_time
        assert not field_value < 0.0
        return field_value

    class Config:  # pylint: disable=missing-class-docstring,too-few-public-methods
        extra = Extra.forbid
