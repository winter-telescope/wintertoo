"""
Module for generating schedules
"""

import logging
from typing import Union

import pandas as pd

from wintertoo.data import get_default_value
from wintertoo.errors import WinterValidationError
from wintertoo.fields import get_best_field, get_field_info
from wintertoo.models import Program
from wintertoo.models.too import (
    AllTooClasses,
    FullTooRequest,
    SummerFieldToO,
    SummerRaDecToO,
    WinterFieldToO,
    WinterRaDecToO,
)
from wintertoo.utils import is_summer
from wintertoo.validate import validate_schedule_df

logger = logging.getLogger(__name__)


def make_schedule(
    toos: list[FullTooRequest],
    program: Program,
    csv_save_file: str = None,
) -> pd.DataFrame:
    """
    Function to build a combined ToO request for several requests.

    :param toos: A list of ToO requests
    :param program: program details
    :param csv_save_file: optional path to export log as csv
    :return: schedule dataframe
    """

    all_entries = []

    for too in toos:
        for filter_name in too.filters:
            for _ in range(too.n_exp):
                new = {
                    "targName": too.target_name,
                    "raDeg": too.ra_deg,
                    "decDeg": too.dec_deg,
                    "fieldID": too.field_id,
                    "filter": filter_name,
                    "visitExpTime": too.t_exp,
                    "priority": too.target_priority,
                    "progPI": program.pi_name,
                    "progName": program.progname,
                    "progID": program.progid,
                    "validStart": too.start_time_mjd,
                    "validStop": too.end_time_mjd,
                    "observed": False,
                    "maxAirmass": too.max_airmass,
                    "ditherNumber": too.n_dither,
                    "ditherStepSize": too.dither_distance,
                    "bestDetector": too.use_best_detector,
                }
                all_entries.append(new)

    schedule = pd.DataFrame(all_entries)
    schedule = schedule.astype({"observed": bool})

    schedule["obsHistID"] = range(len(schedule))

    validate_schedule_df(schedule)

    if csv_save_file is not None:
        logger.info(f"Saving schedule to {csv_save_file}")
        schedule.to_csv(csv_save_file, index=False)
    return schedule


def build_schedule_list(
    too: FullTooRequest,
    program: Program,
    csv_save_file: str = None,
) -> pd.DataFrame:
    """
    Generate a full schedule request for single target,
    with all of RA, Dec and Field ID provided

    :param too: a full ToO request
    :param program: program details
    :param csv_save_file: optional csv save path
    :return: a schedule dataframe
    """
    schedule = make_schedule(
        toos=[too],
        program=program,
        csv_save_file=csv_save_file,
    )
    return schedule


def schedule_ra_dec(
    too: Union[SummerRaDecToO, WinterRaDecToO],
    program: Program,
    csv_save_file: str = None,
) -> pd.DataFrame:
    """
    Generate a schedule for a specific RA/dec pair

    :param too: a ra/dec ToO request
    :param program: program details
    :param csv_save_file: optional csv save path
    :return: a schedule dataframe
    """
    if too.use_field_grid:
        best_field = get_best_field(too.ra_deg, too.dec_deg, summer=is_summer(too))
        too.ra_deg = best_field["RA"]
        too.dec_deg = best_field["Dec"]
        field_id = best_field["ID"]
    else:
        field_id = get_default_value("fieldID")

    full_request = FullTooRequest(field_id=field_id, **too.model_dump())

    schedule = make_schedule(
        toos=[full_request],
        program=program,
        csv_save_file=csv_save_file,
    )

    return schedule


def schedule_field(
    too: Union[SummerFieldToO, WinterFieldToO],
    program: Program,
    csv_save_file: str = None,
) -> pd.DataFrame:
    """
    Generate a schedule for a specific field

    :param too: a field ToO request
    :param program: program details
    :param csv_save_file: optional csv save path
    :return: a schedule dataframe
    """

    summer_bool = is_summer(too)

    field_details = get_field_info(field_id=too.field_id, summer=summer_bool)
    ra_deg = float(field_details["RA"].iloc[0])
    dec_deg = float(field_details["Dec"].iloc[0])

    full_request = FullTooRequest(ra_deg=ra_deg, dec_deg=dec_deg, **too.model_dump())

    schedule = make_schedule(
        toos=[full_request],
        program=program,
        csv_save_file=csv_save_file,
    )

    return schedule


def concat_toos(
    requests: list[AllTooClasses],
    program: Program,
) -> pd.DataFrame:
    """
    Provides a concatenated schedule, composed of multiple individual requests

    :param requests: list of requests
    :param program: program
    :return: schedule dataframe
    """
    schedule = []

    for too in requests:
        if isinstance(too, (SummerFieldToO, WinterFieldToO)):
            res = schedule_field(
                too=too,
                program=program,
            )
        elif isinstance(too, (SummerRaDecToO, WinterRaDecToO)):
            res = schedule_ra_dec(
                too=too,
                program=program,
            )
        else:
            err = f"Unrecognised type {type(too)} for {too}"
            logger.error(err)
            raise WinterValidationError(err)

        schedule.append(res)

    schedule = pd.concat(schedule, ignore_index=True)
    schedule["obsHistID"] = range(len(schedule))
    schedule["fieldID"] = schedule["fieldID"].astype(int)

    return schedule
