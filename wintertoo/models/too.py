from typing import List, Literal, Optional, Union

from astropy.time import Time
from pydantic import BaseModel, Field, validator, Extra

from wintertoo.data import (
    MAX_TARGET_PRIORITY,
    SUMMER_FILTERS,
    WINTER_FILTERS,
    SummerFilters,
    WinterFilters,
    get_default_value,
)
from wintertoo.errors import WinterValidationError


class ToORequest(BaseModel):
    filters: list[str] = Field(min_length=1)
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
    max_airmass: Optional[float] = Field(
        default=get_default_value("maxAirmass"),
        ge=1,
        le=5,
        title="Allowed airmass range",
    )

    @validator("end_time_mjd")
    def validate_field_pairs(cls, field_value, values, field):
        min_key = "start_time_mjd"
        start_time = values[min_key]
        if not field_value > start_time:
            raise WinterValidationError(
                f"{field.name} ({field_value}) not "
                f"greater than {min_key} ({start_time})"
            )
        return field_value

    class Config:
        extra = Extra.forbid


class ObsWithRaDec(BaseModel):
    ra_deg: float = Field(
        title="Right ascension in decimal degrees", ge=0.0, le=360.0, example=180.0
    )
    dec_deg: float = Field(
        title="Declination in decimal degrees", ge=-90.0, le=90.0, example=0.0
    )
    use_field_grid: bool = Field(
        title="boolean whether to select nearest field in grid for central ra/dec",
        default=True,
    )


class ObsWithField(BaseModel):
    field_id: int = Field(title="Field ID", ge=1)


class RaDecToO(ToORequest, ObsWithRaDec):
    """ToO Request with Ra/Dec"""


class FieldToO(ToORequest, ObsWithField):
    """ToO Request with field"""


class FullTooRequest(ToORequest, ObsWithRaDec, ObsWithField):
    pass


class Summer(ToORequest):
    filters: List[SummerFilters] = Field(default=SUMMER_FILTERS)


class Winter(ToORequest):
    filters: list[WinterFilters] = WINTER_FILTERS


class SummerFieldToO(Summer, FieldToO):
    pass


class SummerRaDecToO(Summer, RaDecToO):
    pass


class WinterFieldToO(Winter, FieldToO):
    pass


class WinterRaDecToO(Winter, RaDecToO):
    pass


ALL_TOO_CLASSES = Union[SummerFieldToO, SummerRaDecToO, WinterFieldToO, WinterRaDecToO]
