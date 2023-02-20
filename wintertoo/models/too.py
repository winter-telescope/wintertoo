from typing import Optional

from astropy.time import Time
from pydantic import BaseModel, Field, validator

from wintertoo.data import (
    MAX_TARGET_PRIORITY,
    SUMMER_FILTERS,
    WINTER_FILTERS,
    get_default_value,
)
from wintertoo.validate import WinterValidationError


class ToORequest(BaseModel):
    filters: list[str]
    target_priority: float = Field(
        default=MAX_TARGET_PRIORITY / 2.0,
        title=f"Priority for target",
        le=MAX_TARGET_PRIORITY,
    )
    t_exp: float = Field(
        default=get_default_value("visitExpTime"),
        title="Individual exposure time (s)",
        ge=1.0,
        le=300,
    )
    n_exp: int = Field(default=1, ge=1, title="Number of dither sets")
    n_dither: int = Field(
        default=get_default_value("ditherNumber"), ge=1, title="Number of dithers"
    )
    dither_distance: float = Field(
        get_default_value("ditherStepSize"), ge=0.0, title="dither distance (arcsec)"
    )
    start_time_mjd: Optional[float] = Field(
        default=Time.now().mjd + 0.01,
        title="ToO validity start (MJD)",
    )
    end_time_mjd: Optional[float] = Field(
        default=Time.now().mjd + 1, ge=Time.now().mjd, title="ToO validity end (MJD)"
    )

    @validator("end_time_mjd")
    @classmethod
    def validate_field_pairs(cls, field_value, values, field):
        min_key = "start_time_mjd"
        start_time = values[min_key]
        if not field_value > start_time:
            raise WinterValidationError(
                f"{field.name} ({field_value}) not "
                f"greater than {min_key} ({start_time})"
            )
        return field_value


class TooRequestRaDec(ToORequest):
    ra_deg: float = Field(
        title="Right ascension in decimal degrees", ge=0.0, le=360.0, example=180.0
    )
    dec_deg: float = Field(
        title="Declination in decimal degrees", ge=-90.0, le=90.0, example=0.0
    )


class TooRequestField(ToORequest):
    field_id: int = Field(title="Value of field", ge=1)


class Summer(ToORequest):
    filters: list[str] = SUMMER_FILTERS


class Winter(ToORequest):
    filters: list[str] = WINTER_FILTERS


class SummerToORequestRaDec(Summer, TooRequestRaDec):
    pass


class SummerToORequestField(Summer, TooRequestField):
    pass


class WinterToORequestRaDec(Winter, TooRequestRaDec):
    pass


class WinterToORequestField(Winter, TooRequestField):
    pass
