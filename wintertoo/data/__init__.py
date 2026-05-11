"""
Central module for general data and telescope constants
"""

import json
import typing
from pathlib import Path
from typing import Literal

import astroplan
import pandas as pd
from astropy import units as u
from astropy.coordinates import EarthLocation

data_dir = Path(__file__).parent.resolve()

summer_fields_path = data_dir.joinpath("summer_fields.txt")
summer_fields = pd.read_csv(summer_fields_path, sep=r"\s+")

winter_fields_path = data_dir.joinpath("winter_fields.txt")
all_winter_fields = pd.read_csv(winter_fields_path, sep=r"\s+")
winter_fields = all_winter_fields[all_winter_fields["ID"] < 41170]
winter_secondary_fields = all_winter_fields[all_winter_fields["ID"] >= 41170]

SummerFilters = Literal["u", "g", "r", "i"]
WinterFilters = Literal["dark", "Y", "J", "Hs"]
SpringFilters = Literal["dark", "Y", "J", "Hs"]

SUMMER_FILTERS = list(typing.get_args(SummerFilters))
WINTER_FILTERS = list(typing.get_args(WinterFilters))
WINTER_SCIENCE_FILTERS = ["Y", "J", "Hs"]
SPRING_FILTERS = list(typing.get_args(SpringFilters))
SPRING_SCIENCE_FILTERS = ["Y", "J", "Hs"]

SUMMER_BASE_WIDTH = 0.26112
WINTER_BASE_WIDTH = 1.0
SPRING_BASE_WIDTH = 1.0

MAX_TARGNAME_LEN = 30

WINTER_OVERHEAD = 1.125
SPRING_OVERHEAD = 1.400


def get_overhead(
    camera: Literal["summer", "winter", "spring"],
) -> float:
    """
    Get overhead for a given camera.

    :param camera: Camera to get overhead for
    :return: overhead in hours
    """
    if camera == "summer":
        return 1.0
    if camera == "winter":
        return WINTER_OVERHEAD
    if camera == "spring":
        return SPRING_OVERHEAD

    raise ValueError(f"Unknown camera {camera}")


WinterImageTypes = Literal["exposure", "raw", "science", "stack", "diff", "avro"]
DEFAULT_IMAGE_TYPE = "stack"

too_schedule_config_path = data_dir.joinpath("observing_request_schema.json")

with open(too_schedule_config_path, "rb") as f:
    too_db_schedule_config = json.load(f)


def get_default_value(key: str):
    """
    Get default value for a parameter.

    :param key: Key to check
    :return: default value
    """
    return too_db_schedule_config["properties"][key]["default"]


PALOMAR_LOC = EarthLocation.from_geodetic(-116.863 * u.deg, 33.356 * u.deg, 1706 * u.m)
palomar_observer = astroplan.Observer(location=PALOMAR_LOC)
