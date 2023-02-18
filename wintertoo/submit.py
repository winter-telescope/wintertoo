from datetime import datetime

import pandas as pd
from sqlalchemy import create_engine

from wintertoo.validate import validate_schedule_df, validate_schedule_request


def export_schedule_to_sqlitedb(schedule: pd.DataFrame, base_save_path: str):
    # Validate format of schedule using json schema
    validate_schedule_df(schedule)

    date = datetime.now().strftime("%m_%d_%Y_%H_%s")

    save_path = f"{base_save_path}timed_requests_{date}.db"

    print(f"Saving to {save_path}")

    sqlite_table = "Summary"

    engine = create_engine(f"sqlite:///{save_path}?check_same_thread=False", echo=True)
    schedule.to_sql(sqlite_table, engine, if_exists="replace", index=False)


def submit_schedule(
    schedule: pd.DataFrame,
    save_path: str,
    program_api_key: str,
    program_name: str,
    program_db_host: str,
    program_db_user: str,
    program_db_password: str,
):
    validate_schedule_request(
        schedule,
        program_api_key=program_api_key,
        program_name=program_name,
        program_db_user=program_db_user,
        program_db_password=program_db_password,
        program_db_host=program_db_host,
    )
    export_schedule_to_sqlitedb(schedule, save_path)
