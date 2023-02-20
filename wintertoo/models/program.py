from pydantic import BaseModel, Field, validator, Extra


class Program(BaseModel):
    progid: int = Field()
    progname: str = Field(min_length=8, max_length=8, example="2020A000")
    progtitle: str = Field(min_length=1)
    piname: str = Field(min_length=1)
    startdate: str = Field(max_length=10, min_length=10, example="2020-01-01")
    enddate: str = Field(max_length=10, min_length=10, example="2020-01-01")
    time_hours: float = Field(ge=0.0)
    basepriority: float = Field(ge=0.0, example=100.0)
    prog_api_key: str = Field(min_length=1)

    @validator("startdate", "enddate")
    def check_date(cls, value):
        split = value.split("-")
        assert len(split) == 3
        assert len(split[0]) == 4
        assert len(split[1]) == 2
        assert len(split[2]) == 2
        return value

    class Config:
        extra = Extra.forbid
