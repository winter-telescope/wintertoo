"""
Module for database functions
"""

import getpass
import secrets
from typing import Unpack

import bcrypt
import numpy as np
import pandas as pd
import psycopg

from wintertoo.errors import WinterCredentialsError
from wintertoo.models import DatabaseConfig


def get_program_details(  # pylint: disable=R0913,R0914,R0917
    program_name: str, program_api_key: str, **kwargs: Unpack[DatabaseConfig]
) -> pd.DataFrame:
    """
    Get details of chosen program
    :param program_name: Name of program (e.g. 2020A001)
    :param program_api_key: program api key
    :param kwargs: database connection parameters
    :return: dataframe of program
    """

    db_config = DatabaseConfig(**kwargs)

    if db_config.db_user is None:
        db_config.db_user = input("Enter program_db_user: ")

    if db_config.db_password is None:
        db_config.db_password = getpass.getpass(
            f"Enter password for db_user {db_config.db_user}: "
        )

    with psycopg.connect(  # pylint: disable=not-context-manager
        dbname=db_config.db_name,
        user=db_config.db_user,
        password=db_config.db_password,
        host=db_config.db_host,
        port=db_config.db_port,
    ) as conn:
        conn.read_only = True
        with conn.execute("SELECT * FROM programs") as cursor:
            colnames = [desc[0] for desc in cursor.description]
            data = pd.DataFrame(cursor.fetchall(), columns=colnames)

    name_match = []

    for name in data["progname"]:
        name_match.append(int(secrets.compare_digest(name, program_name)))

    key_match = []

    for hashed in data["prog_key"]:
        try:
            key_match.append(
                int(
                    bcrypt.checkpw(
                        program_api_key.encode("utf-8"), hashed.encode("utf-8")
                    )
                )
            )
        except ValueError:
            key_match.append(0)

    mask = np.array(name_match) & np.array(key_match)

    if np.sum(mask) == 0:
        raise WinterCredentialsError("Program credentials not found in database")

    data = data.iloc[mask.astype(bool)]

    assert np.sum(mask) == 1, "Found multiple matches in database"

    for col in ["startdate", "enddate"]:
        data[col] = data[col].astype(str)

    return data
