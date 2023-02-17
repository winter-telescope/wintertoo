"""
Module for validating ToO requests
"""
import json
import logging

import astropy.time
import pandas as pd
from astropy import units as u
from astropy.time import Time
from jsonschema import ValidationError, validate

from wintertoo.data import (
    MAX_TARGET_PRIORITY,
    PROGRAM_DB_HOST,
    SUMMER_FILTERS,
    too_db_schedule_config,
)
from wintertoo.utils import get_program_details, up_tonight

logger = logging.getLogger(__name__)


class RequestValidationError(Exception):
    """Error relating to a ToO request validation"""


def validate_schedule_json(data: dict):
    """
    Validates that a schedule json matches the ToO database schema.
    Returns nothing, but raises an error if needed.

    :param data: data to validate
    :return: None
    """
    try:
        validate(data, schema=too_db_schedule_config)
        logger.info("Successfully validated schema")
    except ValidationError as exc:
        logger.error(
            "Error with JSON schema validation, input data not formatted correctly."
        )
        logger.error(exc)
        raise RequestValidationError(exc) from exc


def validate_schedule_df(df: pd.DataFrame):
    """
    Validate a schedule dataframe

    :param df: dataframe
    :return: None
    """
    for _, row in df.iterrows():
        json.loads(row.to_json())
        validate_schedule_json(json.loads(row.to_json()))


def validate_target_visibility(schedule: pd.DataFrame):
    """
    Validate that requested targets in a schedule are visible.
    Returns nothing, but raises errors as required.

    :param schedule: Schedule to check
    :return: None
    """
    for _, row in schedule.iterrows():
        ra = row["raDeg"] * u.deg
        dec = row["decDeg"] * u.deg

        for time_mjd in [row["validStart"], row["validStop"]]:
            t_mjd = Time(time_mjd, format="mjd")

            is_up, _ = up_tonight(time_mjd=t_mjd, ra=ra, dec=dec)

            if not is_up:
                err = (
                    f"The following target is not visible on requested date {t_mjd}: \n"
                    f" {row}"
                )
                logger.error(err)
                raise RequestValidationError(err)


def calculate_overall_priority(
    target_priority: float, program_base_priority: float
) -> float:
    """
    Calculate the overall priority for a target

    :param target_priority: User-assigned priority
    :param program_base_priority: Underlying program priority
    :return: overall priority
    """
    return target_priority + program_base_priority


def validate_target_priority(schedule: pd.DataFrame, program_base_priority: float):
    """
    Validates the priority assigned to each target does not exceed
    the maximum allowed for the particular program. If not, raises an error.

    :param schedule: schedule to check
    :param program_base_priority: base priority of program
    :return: None.
    """
    max_priority = calculate_overall_priority(
        target_priority=MAX_TARGET_PRIORITY, program_base_priority=program_base_priority
    )

    for _, row in schedule.iterrows():
        target_priority = float(row["priority"])

        if target_priority > max_priority:
            err = (
                f"Target priority ({target_priority} exceeds maximum allowed value "
                f"of {max_priority}. The maximum is the sum of the "
                f"overall max target priority ({MAX_TARGET_PRIORITY}) "
                f"and the program priority ({program_base_priority})."
            )
            logger.error(err)
            raise RequestValidationError(err)


def validate_filter(filter_name: str):
    """
    Validates that the chosen filters are indeed SUMMER filters. Not case-sensitive.

    :param filter_name: name of filter
    :return:
    """
    assert filter_name.lower() in SUMMER_FILTERS


def validate_target_pi(schedule: pd.DataFrame, prog_pi: str):
    """
    Validate that the program PI matches recorded PI of program.
    Raises an error if not.

    :param schedule: Schedule to check
    :param prog_pi: true program PI
    :return: None.
    """
    for _, row in schedule.iterrows():
        pi = row["progPI"]
        if pi != prog_pi:
            err = f"Pi '{pi}' does not match database PI for program {row['progName']}"
            logger.error(err)
            raise RequestValidationError(err)


def validate_target_dates(
    schedule: pd.DataFrame,
    program_start_date: astropy.time.Time,
    program_end_date: astropy.time.Time,
):
    """
    Validates that the chosen start/stop time for a target are acceptable.
    This includes that the program is still throughout,
    and that the start time is before the end time.
    Raises an error if not.

    :param schedule: Schedule to check
    :param program_start_date: start date of program
    :param program_end_date: end date of program
    :return: None
    """
    for _, row in schedule.iterrows():
        start_time = Time(row["validStart"], format="mjd")
        stop_time = Time(row["validStop"], format="mjd")

        err = None

        if start_time > stop_time:
            err = f"Start time '{start_time}' is after stop time '{stop_time}'."

        elif start_time < program_start_date:
            err = (
                f"Start time '{start_time}' is before program start date '{stop_time}'"
            )

        elif stop_time > program_end_date:
            err = f"Stop time '{start_time}' is after program end date '{stop_time}'"

        if err is not None:
            logger.error(err)
            raise RequestValidationError(err)


def validate_schedule_request(
    schedule_request: pd.DataFrame,
    program_api_key: str,
    program_db_user: str = None,
    program_db_password: str = None,
    program_db_host_name: str = PROGRAM_DB_HOST,
):
    """
    Central to validate that a schedule request is allowed.
    Raises an error if not.

    :param schedule_request: Schedule to validate
    :param program_api_key: unique API key for program
    :param program_db_user:  user for the programs database
    :param program_db_password: password for the programs database
    :param program_db_host_name: host of the programs database
    :return: None
    """
    validate_schedule_df(schedule_request)
    validate_target_visibility(schedule_request)
    prog_names = list(set(schedule_request["progName"]))
    for program_name in prog_names:
        res = schedule_request[schedule_request["progName"] == program_name]

        # Check request using program info
        programs_query_results = get_program_details(
            program_name,
            program_api_key=program_api_key,
            db_user=program_db_user,
            db_password=program_db_password,
            db_host=program_db_host_name,
        )

        if len(programs_query_results) == 0:
            raise ValidationError(
                f"Found no match in program database for program {program_name}"
            )

        if len(programs_query_results) > 1:
            raise ValidationError(
                f"Found multiple matches in program database for {program_name}:"
                f" \n {programs_query_results}"
            )

        program_pi = programs_query_results["piname"].iloc[0].strip()
        validate_target_pi(res, prog_pi=program_pi)

        program_base_priority = programs_query_results["basepriority"].iloc[0]
        validate_target_priority(res, program_base_priority=program_base_priority)

        program_start_date = Time(
            str(programs_query_results["startdate"].iloc[0]), format="isot"
        )

        program_end_date = Time(
            str(programs_query_results["enddate"].iloc[0]), format="isot"
        )

        validate_target_dates(
            res,
            program_start_date=program_start_date,
            program_end_date=program_end_date,
        )
