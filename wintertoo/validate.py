import logging
import numpy as np
import pandas as pd
import json
from astropy import units as u
from jsonschema import validate, ValidationError
from wintertoo.data import too_db_schedule_config, summer_filters, max_target_priority
from wintertoo.utils import get_program_details, get_tonight, up_tonight

logger = logging.getLogger(__name__)


class RequestValidationError(Exception):
    pass


def validate_schedule_json(
    data: dict
):
    try:
        validate(data, schema=too_db_schedule_config)
        logger.info("Successfully validated schema")
    except ValidationError as e:
        logger.error("Error with JSON schema validation, input data not formatted correctly.")
        logger.error(e)
        raise RequestValidationError(e)

def validate_schedule_request(
        schedule_request: pd.DataFrame,
        program_name: str,
        program_pi: str,
):
    validate_schedule_df(schedule_request)
    validate_target_visility(schedule_request)

    # Check request using program info

    programs_query_results = get_program_details(program_name)
    program_details = programs_query_results[0]
    program_base_priority = programs_query_results[0][6]

    validate_pi(program_name, pi_name, program_details)
    validate_program_dates(start_time.mjd, stop_time.mjd, program_details)
    validate_target_priority(schedule_request, program_base_priority=program_base_priority)


def validate_schedule_df(
    df: pd.DataFrame
):
    for _, row in df.iterrows():
        json.loads(row.to_json())
        validate_schedule_json(json.loads(row.to_json()))

def validate_schedule_visility(
        schedule: pd.DataFrame
):
    for _, row in schedule.iterrows():

        ra = row["RA"] * u.radians
        dec = row["Dec"] * u.radians

        for time_mjd in [row["validStart"], row["validStop"]]:
            t = Time(time_mjd, format=mjd)

            is_up, _ = up_tonight(time=t, ra=ra, dec=dec)

            if not is_up:
                err = f"The following target is not visible on requested date {t}: \n" \
                      f" {row}"
                logger.error(err)
                raise RequestValidationError(err)


def calculate_overall_priority(
        target_priority: float,
        program_base_priority: float
):
    return target_priority + program_base_priority

def validate_target_priority(
        schedule: pd.DataFrame,
        program_base_priority: float
):
    max_priority = calculate_overall_priority(
        target_priority=max_target_priority,
        program_base_priority=program_base_priority
    )

    for _, row in schedule.iterrows():
        target_priority = schedule["priority"]

        if target_priority > max_priority:
            err = f"Target priority ({target_priority} exceeds maximum allowed value of {target_priority}." \
                  f"The maximum is the sum of the overall max target priority ({max_target_priority}) " \
                  f"and the program priority ({program_base_priority})."
            logger.error(err)
            raise RequestValidationError(err)


def validate_filter(
        filter_name: str
):
    assert filter_name in summer_filters


def validate_pi(
        programs_details,
        program_name: str,
        pi: str
):
    if pi != programs_details[0][2]:
        err = f"Pi '{pi}' does not match PI for program {program_name}"
        logger.error(err)
        raise RequestValidationError(err)


def validate_program_dates(start_time, stop_time, program_details):
    program_start_date = program_details[3]
    program_end_date = program_details[4]
    valid = 0
    if np.logical_or((start_time < program_start_date), (stop_time > program_end_date)):
        valid = -99
        raise RequestValidationError

    return valid


