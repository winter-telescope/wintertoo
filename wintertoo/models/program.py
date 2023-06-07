"""
Base model for the program database

Duplicated (sorry) from mirar/pipelines/summer/models/program.py, to avoid
an elaborate web of imports for WSP.
"""
from pydantic import BaseModel, Field, validator, Extra
from datetime import date

_LEN_PROG_KEY = 60


class ProgramCredentials(BaseModel):
    """
    Program credentials to access a program
    """

    progname: str = Field(min_length=8, max_length=8, example="2020A000")
    prog_key: str = Field(min_length=_LEN_PROG_KEY, max_length=_LEN_PROG_KEY)


class Program(ProgramCredentials):
    """
    A pydantic model for a program database entry
    """

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

    class Config:
        extra = Extra.forbid

# from pydantic import BaseModel, Extra, Field, validator
#
#
# class ProgramCredentials(BaseModel):
#     progname: str = Field(min_length=8, max_length=8, example="2020A000")
#     prog_api_key: str = Field(min_length=1)
#
#
# class Program(ProgramCredentials):
#     progid: int = Field()
#     progtitle: str = Field(min_length=1)
#     piname: str = Field(min_length=1)
#     startdate: str = Field(max_length=10, min_length=10, example="2020-01-01")
#     enddate: str = Field(max_length=10, min_length=10, example="2020-01-01")
#     time_hours_total: float = Field(ge=0.0)
#     hours_remaining: float = Field(ge=0.0)
#     basepriority: float = Field(ge=0.0, example=100.0)
#
#     @validator("startdate", "enddate")
#     def check_date(cls, value):
#         split = value.split("-")
#         assert len(split) == 3
#         assert len(split[0]) == 4
#         assert len(split[1]) == 2
#         assert len(split[2]) == 2
#         return value
#
#     class Config:
#         extra = Extra.forbid
