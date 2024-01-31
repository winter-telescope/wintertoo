"""
Module for validating ToO requests
"""

import json
import logging

import astropy.time
import pandas as pd
from astropy import units as u
from astropy.time import Time
from jsonschema import validate

from wintertoo.data import PROGRAM_DB_HOST, SUMMER_FILTERS, too_db_schedule_config
from wintertoo.database import get_program_details
from wintertoo.errors import WinterCredentialsError, WinterValidationError
from wintertoo.models import Program
from wintertoo.utils import up_tonight

logger = logging.getLogger(__name__)


def get_and_validate_program_details(  # pylint: disable=too-many-arguments
    program_name: str,
    program_api_key: str,
    program_db_user: str = None,
    program_db_password: str = None,
    program_db_host: str = PROGRAM_DB_HOST,
    program_db_name: str = "summer",
) -> Program:
    """
    Get details of chosen program
    :param program_name: Name of program (e.g. 2020A001)
    :param program_api_key: program api key
    :param program_db_user: user of program database
    :param program_db_password: password of program database
    :param program_db_host: host of program database
    :param program_db_name: name of database containing program table
    :return: dataframe of program
    """
    data = get_program_details(
        program_name=program_name,
        program_api_key=program_api_key,
        program_db_user=program_db_user,
        program_db_password=program_db_password,
        program_db_host=program_db_host,
        program_db_name=program_db_name,
    )

    if len(data) == 0:
        raise WinterCredentialsError(
            f"Found no match in program database for combination of "
            f"program={program_name} and api_key"
        )

    if len(data) > 1:
        raise WinterCredentialsError(
            f"Found multiple matches in program database for combination of "
            f"program={program_name} and api_key"
        )

    return Program(**data.iloc[0].to_dict())


def validate_schedule_json(data: dict):
    """
    Validates that a schedule json matches the ToO database schema.
    Returns nothing, but raises an error if needed.
    :param data: data to validate
    :return: None
    """
    try:
        validate(data, schema=too_db_schedule_config)
        logger.debug("Successfully validated schema")
    except WinterValidationError as exc:
        logger.error(
            "Error with JSON schema validation, input data not formatted correctly."
        )
        logger.error(exc)
        raise WinterValidationError(exc) from exc


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
                raise WinterValidationError(err)


def validate_obshist(schedule: pd.DataFrame):
    """
    Ensures that each entry in a schedule has a unique obsHistID, starting at 0.

    :param schedule: Schedule to test
    :return: None
    """

    unique_ids = set(schedule["obsHistID"].tolist())
    if len(schedule) != len(unique_ids):
        err = (
            f"Each entry in schedule needs a unique 'obsHistID'. "
            f"Here there are {len(unique_ids)} unique entries for "
            f"{len(schedule)} entries."
        )
        logger.error(err)
        raise WinterValidationError(err)
    if min(unique_ids) != 0:
        err = (
            f"obsHistID values should start at zero. "
            f"Instead the minimum value is {min(unique_ids)}."
        )
        logger.error(err)
        raise WinterValidationError(err)


def validate_target_priority(schedule: pd.DataFrame, max_priority: float):
    """
    Validates the priority assigned to each target does not exceed
    the maximum allowed for the particular program. If not, raises an error.
    :param schedule: schedule to check
    :param max_priority: base priority of program
    :return: None.
    """

    for _, row in schedule.iterrows():
        target_priority = float(row["priority"])

        if target_priority > max_priority:
            err = (
                f"Target priority ({target_priority} exceeds maximum allowed value "
                f"of {max_priority}. "
            )
            logger.error(err)
            raise WinterValidationError(err)


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
            raise WinterValidationError()


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
            err = (
                f"Start time '{start_time.isot}' is after stop time '{stop_time.isot}'."
            )

        elif start_time < program_start_date:
            err = (
                f"Start time '{start_time.isot}' is before "
                f"program start date '{program_start_date.isot}'"
            )

        elif stop_time > program_end_date:
            err = (
                f"Stop time '{start_time.isot}' is after "
                f"program end date '{program_end_date.isot}'"
            )

        if err is not None:
            logger.error(err)
            raise WinterValidationError(err)


def validate_time_allocation(
    schedule: pd.DataFrame, hours_allocated: float, hours_used: float
):
    """
    Validates that the hours used in the schedule do not exceed hours allocated

    :param schedule: Schedule to check
    :param hours_allocated: hours allocated to the program
    :param hours_used: hours used by the program
    :return: None
    """

    new_hours_used = schedule["visitExpTime"].sum() / 3600
    total_hours_used = new_hours_used + hours_used

    if total_hours_used > hours_allocated:
        err = (
            f"Sum ({total_hours_used}) of hours used ({hours_used}) "
            f"and request duration ({new_hours_used}) "
            f"exceeds hours allocated ({hours_allocated})."
        )
        logger.error(err)
        raise WinterValidationError(err)


def validate_schedule_with_program(  # pylint: disable=too-many-arguments
    schedule_request: pd.DataFrame,
    program: Program,
):
    """
    Big function to validate a schedule request against a program.

    :param schedule_request: Schedule to validate
    :param program: Program to validate against
    :return: None
    """
    validate_schedule_df(schedule_request)
    validate_target_visibility(schedule_request)
    validate_obshist(schedule_request)

    prog_names = list(set(schedule_request["progName"]))
    assert len(prog_names) == 1

    validate_target_pi(schedule_request, prog_pi=program.pi_name)

    validate_target_priority(
        schedule=schedule_request, max_priority=program.maxpriority
    )

    validate_time_allocation(
        schedule=schedule_request,
        hours_allocated=program.hours_allocated,
        hours_used=program.hours_used,
    )

    program_start_date = Time(str(program.startdate), format="isot")

    program_end_date = Time(str(program.enddate), format="isot")

    validate_target_dates(
        schedule_request,
        program_start_date=program_start_date,
        program_end_date=program_end_date,
    )


def validate_schedule_request(  # pylint: disable=too-many-arguments
    schedule_request: pd.DataFrame,
    program_name: str,
    program_api_key: str,
    program_db_name: str,
    program_db_user: str = None,
    program_db_password: str = None,
    program_db_host: str = PROGRAM_DB_HOST,
):
    """
    Central to validate that a schedule request is allowed.
    Raises an error if not.

    :param schedule_request: Schedule to validate
    :param program_name: name of program e.g 2020A000
    :param program_api_key: unique API key for program
    :param program_db_name: name of the programs database
    :param program_db_user:  user for the programs database
    :param program_db_password: password for the programs database
    :param program_db_host: host of the programs database
    :return: None
    """

    # Check request using program info
    program = get_and_validate_program_details(
        program_name=program_name,
        program_api_key=program_api_key,
        program_db_name=program_db_name,
        program_db_user=program_db_user,
        program_db_password=program_db_password,
        program_db_host=program_db_host,
    )

    validate_schedule_with_program(schedule_request, program)
