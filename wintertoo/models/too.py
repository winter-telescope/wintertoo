"""
Models for ToO requests
"""

from typing import List, Optional, Union

from astropy.time import Time
from pydantic import (
    AliasChoices,
    BaseModel,
    ConfigDict,
    Field,
    computed_field,
    model_validator,
)

from wintertoo.data import (
    MAX_TARGNAME_LEN,
    SUMMER_FILTERS,
    WINTER_SCIENCE_FILTERS,
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
    target_name: Optional[str] = Field(
        title="Name of the target",
        min_length=1,
        max_length=MAX_TARGNAME_LEN,
        examples=["SN2021abc", "ZTF19aapreis"],
        default=get_default_value("targName"),
    )
    total_exposure_time: float = Field(
        default=get_default_value("visitExpTime"),
        title="Combined Exposure Time across dithers (s)",
        ge=1.0,
        validation_alias=AliasChoices("total_exposure_time", "t_exp"),
    )
    n_dither: int = Field(
        default=get_default_value("ditherNumber"), ge=1, title="Number of dithers"
    )
    n_repetitions: int = Field(
        default=1,
        ge=1,
        title="Number of repeated dither sets",
        validation_alias=AliasChoices("n_repetitions", "n_exp"),
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
    use_best_detector: bool = Field(
        default=get_default_value("bestDetector"),
        title="Place ra/dec at the center of the best detector",
    )

    @computed_field
    @property
    def single_exposure_time(self) -> float:
        """
        Computed field to get the exposure time per dither.
        Equivalent to total_exposure_time/n_dither

        :return: Exposure time per dither
        """
        return self.total_exposure_time / self.n_dither

    @model_validator(mode="after")
    def validate_end_time(self):
        """
        Field validator to ensure that the end time is greater than the start time

        :return: validated field value
        """
        start_time = self.start_time_mjd
        end_time_mjd = self.end_time_mjd
        if end_time_mjd <= start_time:
            raise WinterValidationError(
                f"end_time_mjd ({end_time_mjd}) not "
                f"greater than start_time_mjd ({start_time})"
            )
        return self

    @model_validator(mode="after")
    def validate_t_exp(self):
        """
        Field validator to ensure that the exposure time is not too long

        :return: Validated total exposure time per dither set
        """
        n_dithers = self.n_dither
        t_exp = self.total_exposure_time
        t_per_dither = t_exp / n_dithers

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

        return self

    model_config = ConfigDict(extra="forbid")


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
        default=False,
    )

    @model_validator(mode="after")
    def validate_field_best_detector(self):
        """
        Field validator to ensure that the end time is greater than the start time

        :return: validated field value
        """
        if self.use_best_detector & self.use_field_grid:
            raise WinterValidationError(
                "Cannot use both use_best_detector and use_field_grid"
            )
        return self


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

    filters: list[WinterFilters] = WINTER_SCIENCE_FILTERS


class SummerFieldToO(Summer, FieldToO):
    """Summer ToO Request with field"""


class SummerRaDecToO(Summer, RaDecToO):
    """Summer ToO Request with Ra/Dec"""


class WinterFieldToO(Winter, FieldToO):
    """Winter ToO Request with field"""


class WinterRaDecToO(Winter, RaDecToO):
    """Winter ToO Request with Ra/Dec"""


AllTooClasses = Union[SummerFieldToO, SummerRaDecToO, WinterFieldToO, WinterRaDecToO]
