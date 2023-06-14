"""
Models for ToO requests
"""
from typing import List, Optional, Union

from astropy.time import Time
from pydantic import BaseModel, Extra, Field, root_validator, validator

from wintertoo.data import (
    SUMMER_FILTERS,
    WINTER_FILTERS,
    SummerFilters,
    WinterFilters,
    get_default_value,
)
from wintertoo.errors import WinterValidationError

MIN_EXPOSURE_TIME = 0.28
MAX_EXPOSURE_TIME = 300.0


class ToORequest(BaseModel):
    """
    Base model for ToO requests
    """

    filters: list[str] = Field(min_length=1)
    target_priority: float = Field(
        default=50.0,
        title="Priority for target",
        ge=0.0,
    )
    t_exp: float = Field(
        default=get_default_value("visitExpTime"),
        title="Combined Exposure Time across dithers (s)",
        ge=1.0,
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
    @classmethod
    def validate_field_pairs(cls, field_value, values, field):
        """
        Field validator to ensure that the end time is greater than the start time

        :param field_value: value of the field
        :param values: values of all fields
        :param field: field name
        :return: validated field value
        """
        min_key = "start_time_mjd"
        start_time = values[min_key]
        if not field_value > start_time:
            raise WinterValidationError(
                f"{field.name} ({field_value}) not "
                f"greater than {min_key} ({start_time})"
            )
        return field_value

    @classmethod
    @root_validator
    def validate_t_exp(cls, values):
        """
        Field validator to ensure that the exposure time is not too long

        :param values: Values of all fields
        :return: Validated total exposure time per dither set
        """
        n_dithers = values["n_dither"]
        t_exp = values["t_exp"]
        t_per_dither = values["t_exp"] / n_dithers

        if t_per_dither > MAX_EXPOSURE_TIME:
            raise WinterValidationError(
                f"t_exp ({t_exp}) is too long for {n_dithers} dithers. "
                f"Max exposure time per dither is {MAX_EXPOSURE_TIME} s, "
                f"while you have selected {t_per_dither} s per dither"
            )

        if t_per_dither < MIN_EXPOSURE_TIME:
            raise WinterValidationError(
                f"t_exp ({t_exp}) is too short for {n_dithers} dithers. "
                f"Min exposure time per dither is {MIN_EXPOSURE_TIME} s, "
                f"while you have selected {t_per_dither} s per dither"
            )
        return values

    class Config:  # pylint: disable=missing-class-docstring,too-few-public-methods
        extra = Extra.forbid


class ObsWithRaDec(BaseModel):
    """
    Base model for ToO requests with Ra/Dec
    """

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
    """
    Base model for ToO requests with field
    """

    field_id: int = Field(title="Field ID", ge=1)


class RaDecToO(ToORequest, ObsWithRaDec):
    """ToO Request with Ra/Dec"""


class FieldToO(ToORequest, ObsWithField):
    """ToO Request with field"""


class FullTooRequest(ToORequest, ObsWithRaDec, ObsWithField):
    """Full ToO Request with field and Ra/Dec"""


class Summer(ToORequest):
    """Summer ToO Request"""

    filters: List[SummerFilters] = Field(default=SUMMER_FILTERS)


class Winter(ToORequest):
    """Winter ToO Request"""

    filters: list[WinterFilters] = WINTER_FILTERS


class SummerFieldToO(Summer, FieldToO):
    """Summer ToO Request with field"""


class SummerRaDecToO(Summer, RaDecToO):
    """Summer ToO Request with Ra/Dec"""


class WinterFieldToO(Winter, FieldToO):
    """Winter ToO Request with field"""


class WinterRaDecToO(Winter, RaDecToO):
    """Winter ToO Request with Ra/Dec"""


AllTooClasses = Union[SummerFieldToO, SummerRaDecToO, WinterFieldToO, WinterRaDecToO]
