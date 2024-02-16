"""
Base models for image queries
"""

from typing import Optional

from astropy import units as u
from astropy.time import Time
from pydantic import BaseModel, Field, model_validator

from wintertoo.data import DEFAULT_IMAGE_TYPE, MAX_TARGNAME_LEN, WinterImageTypes
from wintertoo.errors import WinterValidationError
from wintertoo.utils import get_date


class ImagePath(BaseModel):
    """
    Base model for image paths
    """

    path: str = Field(title="Path to image", min_length=1, example="path/to/image.fits")


class ProgramImageQuery(BaseModel):
    """
    Base model for image queries
    """

    program_name: str = Field(
        title="Program to search for", min_length=1, examples=["2020A000", "2021B001"]
    )
    start_date: int = Field(
        title="Start date for images",
        default=get_date(Time.now() - 30.0 * u.day),
        examples=[get_date(Time.now() - 30.0 * u.day), "20230601"],
    )
    end_date: int = Field(
        title="End date for images",
        default=get_date(Time.now()),
        examples=[get_date(Time.now() - 30.0 * u.day), get_date(Time.now())],
    )
    kind: WinterImageTypes = Field(
        default=DEFAULT_IMAGE_TYPE, example="raw/science/diff"
    )

    @model_validator(mode="after")
    def validate_date_order(self):
        """
        Ensure that the start date is before the end date

        :return: validated field value
        """
        if self.start_date > self.end_date:
            raise WinterValidationError("Start date is after end date")

        today = get_date(Time.now())

        if self.start_date > today:
            raise WinterValidationError(
                f"Start date is in the future, (today is {today})"
            )

        if self.end_date > today:
            raise WinterValidationError(
                f"End date is in the future, (today is {today})"
            )

        return self


class TargetImageQuery(ProgramImageQuery):
    """
    Model for image queries based on target name
    """

    target_name: Optional[str] = Field(
        title="Name of target",
        min_length=1,
        max_length=MAX_TARGNAME_LEN,
        examples=["SN2023ixf", "ZTF19aapreis"],
    )


class RectangleImageQuery(ProgramImageQuery):
    """
    Model for image queries with a rectangular region
    """

    ra_min: float = Field(
        title="Minimum RA (degrees)", ge=0.0, le=360.0, examples=[90.0, 180.0]
    )
    ra_max: float = Field(
        title="Minimum RA (degrees)", ge=0.0, le=360.0, examples=[90.0, 180.0]
    )

    dec_min: float = Field(
        title="Minimum dec (degrees)", ge=-90.0, le=90.0, examples=[-30.0, 10.0]
    )
    dec_max: float = Field(
        title="Minimum dec (degrees)", ge=-90.0, le=90.0, examples=[-30.0, 10.0]
    )

    @model_validator(mode="after")
    def validate_field_pairs(self):
        """
        Validate that the max value is greater than the min value

        :return: validated field value
        """

        pairs = [
            (self.ra_min, self.ra_max, "RA"),
            (self.dec_min, self.dec_max, "Dec"),
        ]
        for min_val, max_val, label in pairs:
            if max_val <= min_val:
                raise WinterValidationError(
                    f"{label} range invalid: maximum value ({max_val}) not "
                    f"greater than minimum value({min_val})"
                )
        return self


class ConeImageQuery(ProgramImageQuery):
    """
    Model for image queries with a circular region
    """

    ra: float = Field(
        title="Center RA (degrees)", ge=0.0, le=360.0, examples=[90.0, 180.0]
    )
    dec: float = Field(
        title="Center dec (degrees)", ge=-90.0, le=90.0, examples=[-30.0, 10.0]
    )
    radius_deg: float = Field(
        title="Search radius in degrees", ge=0.0, le=90.0, default=1.0
    )
