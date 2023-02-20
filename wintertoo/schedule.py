"""
Module for generating schedules
"""
import logging

import pandas as pd
from astropy import units as u
from astropy.time import Time

from wintertoo.data import SUMMER_FILTERS, WINTER_FILTERS, get_default_value
from wintertoo.fields import get_best_field, get_field_info
from wintertoo.models.too import TooRequestField, TooRequestRaDec
from wintertoo.validate import calculate_overall_priority, validate_schedule_df

logger = logging.getLogger(__name__)


# pylint: disable=too-many-arguments,too-many-locals
def make_schedule(
    ra_degs: list,
    dec_degs: list,
    field_ids: list,
    start_times: list,
    end_times: list,
    program_name: str,
    program_id: int,
    pi: str,
    program_priority: float = 0.0,
    filters: list = None,
    texp: float = get_default_value("visitExpTime"),
    nexp: int = 1,
    n_dither: int = get_default_value("ditherNumber"),
    dither_distance: float = get_default_value("ditherStepSize"),
    maximum_airmass: float = get_default_value("maxAirmass"),
    target_priorities: list = None,
    csv_save_file: str = None,
) -> pd.DataFrame:
    """
    Function to build a combined ToO request for several requests.
    :param ra_degs: list of RAs
    :param dec_degs: list of decs
    :param field_ids: list of field IDs
    :param start_times: List of validity start times
    :param end_times: list of validity end times
    :param program_name: program name
    :param program_id: program ID
    :param pi: Program PI
    :param program_priority: Base program priority
    :param filters: list of filters per target
    :param texp: exposure time
    :param nexp: number of dither sequences per target
    :param n_dither: number of dithers per target
    :param dither_distance: spacing (arcsec) of dither grid
    :param maximum_airmass: maximum airmass per target
    :param target_priorities: list of target priorities
    :param csv_save_file: optional path to export log as csv
    :return: schedule dataframe
    """
    if filters is None:
        filters = SUMMER_FILTERS

    all_entries = []

    for i, ra_deg in enumerate(ra_degs):
        dec_deg = dec_degs[i]
        field_id = field_ids[i]
        start_time = start_times[i]
        end_time = end_times[i]

        priority = calculate_overall_priority(
            target_priority=target_priorities[i], program_base_priority=program_priority
        )

        for filter_name in filters:
            for _ in range(nexp):
                new = {
                    "raDeg": ra_deg,
                    "decDeg": dec_deg,
                    "fieldID": field_id,
                    "filter": filter_name,
                    "visitExpTime": texp,
                    "priority": priority,
                    "progPI": pi,
                    "progName": program_name,
                    "progID": program_id,
                    "validStart": start_time.mjd,
                    "validStop": end_time.mjd,
                    "observed": False,
                    "maxAirmass": maximum_airmass,
                    "ditherNumber": n_dither,
                    "ditherStepSize": dither_distance,
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
    ra_deg: float,
    dec_deg: float,
    field_id: int,
    pi: str,
    program_name: str,
    program_id: int,
    target_priority: float,
    program_priority: float,
    t_exp: float,
    n_exp: int,
    n_dither: int,
    dither_distance: float,
    start_time: Time,
    end_time: Time,
    summer: bool = True,
    filters=None,
    csv_save_file: str = None,
):
    """
    Generate a full schedule request for single target,
    with RA, Dec and Field ID required

    :param ra_deg: RA
    :param dec_deg: dec
    :param field_id: field ID
    :param pi: Name of program PI
    :param program_name: Name of program
    :param program_id: Program ID -> interger for survey/Caltech/MIT/engineering
    :param target_priority: Priority for the target
    :param program_priority: Base priority for the program
    :param filters: filters to use
    :param t_exp: Length of each exposure (s)
    :param n_exp: Number of dither sets
    :param n_dither: Number of dithers per cycle
    :param dither_distance: spacing (arcsec) of dither grid
    :param start_time: start time of validity window
    :param end_time: end time of validity window
    :param summer: boolean whether to use summer (rather than winter)
    :param csv_save_file: optional csv save path
    :return: a schedule dataframe
    """
    if summer:
        default_filters = SUMMER_FILTERS
    else:
        default_filters = WINTER_FILTERS

    if filters is None:
        logger.info(f"No filters specified. Using all as default: {default_filters}.")
        filters = default_filters
    if not isinstance(filters, list):
        filters = [filters]

    for filter_name in filters:
        assert filter_name in default_filters

    schedule = make_schedule(
        ra_degs=[ra_deg],
        dec_degs=[dec_deg],
        field_ids=[field_id],
        start_times=[start_time],
        end_times=[end_time],
        filters=filters,
        target_priorities=[target_priority],
        texp=t_exp,
        nexp=n_exp,
        n_dither=n_dither,
        dither_distance=dither_distance,
        pi=pi,
        program_priority=program_priority,
        program_name=program_name,
        program_id=program_id,
        csv_save_file=csv_save_file,
    )
    return schedule


def schedule_ra_dec(
    ra_deg: float,
    dec_deg: float,
    pi: str,
    program_name: str,
    program_id: int,
    target_priority: float = 1.0,
    program_priority: float = 0.0,
    filters=None,
    t_exp: float = get_default_value("visitExpTime"),
    n_exp: int = 1,
    n_dither: int = get_default_value("ditherNumber"),
    dither_distance: float = get_default_value("ditherStepSize"),
    start_time: Time = Time.now(),
    end_time: Time = Time.now() + 1.0 * u.day,
    summer: bool = True,
    use_field: bool = True,
    csv_save_file: str = None,
) -> pd.DataFrame:
    """
    Generate a schedule for a specific RA/dec pair
    :param ra_deg: RA
    :param dec_deg: dec
    :param pi: Name of program PI
    :param program_name: Name of program
    :param program_id: Program ID -> interger for survey/Caltech/MIT/engineering
    :param target_priority: Priority for the target
    :param program_priority: Base priority for the program
    :param filters: filters to use
    :param t_exp: Length of each exposure (s)
    :param n_exp: Number of dither sets
    :param n_dither: Number of dithers per cycle
    :param dither_distance: spacing (arcsec) of dither grid
    :param start_time: start time of validity window
    :param end_time: end time of validity window
    :param summer: boolean whether to use summer (rather than winter)
    :param use_field: boolean to select a field close to the
    :param csv_save_file: optional csv save path
    :return: a schedule dataframe
    """

    if use_field:
        best_field = get_best_field(ra_deg, dec_deg, summer=summer)
        ra_deg = best_field["RA"]
        dec_deg = best_field["Dec"]
        field_id = best_field["ID"]
    else:
        field_id = get_default_value("fieldID")

    schedule = build_schedule_list(
        ra_deg=ra_deg,
        dec_deg=dec_deg,
        field_id=field_id,
        start_time=start_time,
        end_time=end_time,
        filters=filters,
        target_priority=target_priority,
        t_exp=t_exp,
        n_exp=n_exp,
        n_dither=n_dither,
        dither_distance=dither_distance,
        pi=pi,
        program_priority=program_priority,
        program_name=program_name,
        program_id=program_id,
        csv_save_file=csv_save_file,
    )

    return schedule


def schedule_field(
    field_id: int,
    pi: str,
    program_name: str,
    program_id: int,
    target_priority: float = 1.0,
    program_priority: float = 0.0,
    filters=None,
    t_exp: float = get_default_value("visitExpTime"),
    n_exp: int = 1,
    n_dither: int = get_default_value("ditherNumber"),
    dither_distance: float = get_default_value("ditherStepSize"),
    start_time: Time = Time.now(),
    end_time: Time = Time.now() + 1.0 * u.day,
    summer: bool = True,
    csv_save_file: str = None,
) -> pd.DataFrame:
    """
    Generate a schedule for a specific field
    :param field_id: field ID
    :param pi: Name of program PI
    :param program_name: Name of program
    :param program_id: Program ID -> interger for survey/Caltech/MIT/engineering
    :param target_priority: Priority for the target
    :param program_priority: Base priority for the program
    :param filters: filters to use
    :param t_exp: Length of each exposure (s)
    :param n_exp: Number of dither sets
    :param n_dither: Number of dithers per cycle
    :param dither_distance: spacing (arcsec) of dither grid
    :param start_time: start time of validity window
    :param end_time: end time of validity window
    :param summer: boolean whether to use summer (rather than winter)
    :param csv_save_file: optional csv save path
    :return: a schedule dataframe
    """
    field_details = get_field_info(field_id=field_id, summer=summer)
    ra_deg = float(field_details["RA"])
    dec_deg = float(field_details["Dec"])

    schedule = build_schedule_list(
        ra_deg=ra_deg,
        dec_deg=dec_deg,
        field_id=field_id,
        start_time=start_time,
        end_time=end_time,
        filters=filters,
        target_priority=target_priority,
        t_exp=t_exp,
        n_exp=n_exp,
        n_dither=n_dither,
        dither_distance=dither_distance,
        pi=pi,
        program_priority=program_priority,
        program_name=program_name,
        program_id=program_id,
        csv_save_file=csv_save_file,
    )

    return schedule
