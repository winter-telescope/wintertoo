"""
Module handling submission of ToO schedules
"""
import logging
from datetime import datetime
from typing import Optional

import pandas as pd
from sqlalchemy import create_engine

from wintertoo.validate import validate_schedule_df, validate_schedule_request

logger = logging.getLogger(__name__)


def export_schedule_to_sqlitedb(schedule: pd.DataFrame, base_save_path: str):
    """
    Function to export a schedule to an sqlite db file

    :param schedule: schedule to export
    :param base_save_path: directory to save to
    :return: None
    """
    # Validate format of schedule using json schema
    validate_schedule_df(schedule)

    date = datetime.now().strftime("%m_%d_%Y_%H_%s")

    save_path = f"{base_save_path}timed_requests_{date}.db"

    logger.info(f"Saving to {save_path}")

    sqlite_table = "Summary"

    engine = create_engine(f"sqlite:///{save_path}?check_same_thread=False", echo=True)
    schedule.to_sql(sqlite_table, engine, if_exists="replace", index=False)


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
):
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

        export_schedule_to_sqlitedb(schedule, save_path)
