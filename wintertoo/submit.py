"""
Module handling submission of ToO schedules
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd
from sqlalchemy import create_engine

from wintertoo.validate import validate_schedule_df, validate_schedule_request

logger = logging.getLogger(__name__)

FILE_DATE_FORMAT = "%Y_%m_%d_%H_%M_%S"


def get_db_file_name(program_name: str, date: Optional[datetime] = None) -> str:
    """
    Function to get the name of a database file

    :param program_name: Name of program
    :param date: Date to use
    :return: String of database file name
    """

    if date is None:
        date = datetime.now()

    strf_time = date.strftime(FILE_DATE_FORMAT)

    return f"request_{program_name}_{strf_time}.db"


def export_schedule_to_sqlitedb(schedule: pd.DataFrame, base_save_path: str) -> Path:
    """
    Function to export a schedule to an sqlite db file

    :param schedule: schedule to export
    :param base_save_path: directory to save to
    :return: None
    """
    # Validate format of schedule using json schema
    validate_schedule_df(schedule)

    program_name = str(schedule["progName"].iloc[0])

    schedule_file_name = get_db_file_name(program_name=program_name)

    save_path = Path(base_save_path).joinpath(schedule_file_name)

    logger.info(f"Saving to {save_path}")

    sqlite_table = "Summary"

    if not save_path.parent.exists():
        err = f"Parent directory {save_path.parent} does not exist"
        logger.error(err)
        raise ValueError(err)

    engine = create_engine(f"sqlite:///{save_path}?check_same_thread=False", echo=True)
    schedule.to_sql(sqlite_table, engine, if_exists="replace", index=False)

    return save_path


def submit_schedule(  # pylint: disable=too-many-arguments
    schedule: pd.DataFrame,
    program_api_key: str,
    program_name: str,
    program_db_name: str,
    program_db_host: str,
    program_db_user: str,
    program_db_password: str,
    save_path: Optional[str] = None,
    submit_trigger: bool = True,
) -> Optional[Path]:
    """
    Function to validate, and then optionally submit, a schedule

    :param schedule: schedule to use
    :param program_api_key: API key of program
    :param program_name: Program name (e.g 2020A000)
    :param program_db_name: Name of program DB
    :param program_db_host: Host of programs DB
    :param program_db_user: User of programs DB
    :param program_db_password: password of programs DB
    :param save_path: save path
    :param submit_trigger: boolean for whether to actually submit a trigger
    :return: None
    """
    validate_schedule_request(
        schedule,
        program_api_key=program_api_key,
        program_name=program_name,
        program_db_name=program_db_name,
        program_db_user=program_db_user,
        program_db_password=program_db_password,
        program_db_host=program_db_host,
    )
    if submit_trigger:
        if save_path is None:
            err = "Save path cannot be None if submission is planned"
            logger.error(err)
            raise ValueError(err)

        return export_schedule_to_sqlitedb(schedule, save_path)

    return None
