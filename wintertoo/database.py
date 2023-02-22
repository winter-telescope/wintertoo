import getpass

import numpy as np
import pandas as pd
import psycopg

from wintertoo.data import PROGRAM_DB_HOST


def get_program_details(  # pylint: disable=too-many-arguments
    program_name: str,
    program_api_key: str,
    program_db_user: str = None,
    program_db_password: str = None,
    program_db_host: str = PROGRAM_DB_HOST,
    program_db_name: str = "summer",
) -> pd.DataFrame:
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

    if program_db_user is None:
        program_db_user = input("Enter program_db_user: ")

    if program_db_password is None:
        program_db_password = getpass.getpass(
            f"Enter password for program_db_user {program_db_user}: "
        )

    with psycopg.connect(  # pylint: disable=not-context-manager
        f"dbname='{program_db_name}' user={program_db_user} "
        f"password={program_db_password} host={program_db_host}",
    ) as conn:
        conn.read_only = True
        with conn.execute("SELECT * FROM programs") as cursor:
            colnames = [desc[0] for desc in cursor.description]
            data = cursor.fetchall()
            data = pd.DataFrame(data, columns=colnames)

    mask = np.logical_and(
        data["prog_api_key"] == program_api_key, data["progname"] == program_name
    )
    data = data[mask]

    for col in ["startdate", "enddate"]:
        data[col] = data[col].astype(str)

    data.drop("id", inplace=True, axis=1)

    return data
