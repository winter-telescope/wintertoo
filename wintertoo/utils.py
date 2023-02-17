#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jan 25 13:51:59 2022
@author: frostig, belatedly edited by Robert Stein
"""
import getpass
import logging

import astropy.time
import numpy as np
import pandas as pd
import psycopg
from astropy.coordinates import AltAz, SkyCoord
from astropy.time import Time

from wintertoo.data import PALOMAR_LOC, PROGRAM_DB_HOST, palomar_observer

logger = logging.getLogger(__name__)

MINIMUM_ELEVATION = 20.0


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
        f"password={program_db_password} host={program_db_host}"
    ) as conn:
        command = (
            f"SELECT * FROM programs "
            f"WHERE programs.progname = '{program_name}' AND "
            f"programs.prog_api_key = '{program_api_key}';"
        )
        with conn.execute(command) as cursor:
            colnames = [desc[0] for desc in cursor.description]
            data = cursor.fetchall()
            data = pd.DataFrame(data, columns=colnames)

    for col in ["startdate", "enddate"]:
        data[col] = data[col].astype(str)

    data.drop("id", inplace=True, axis=1)
    data["prog_api_key"] = program_api_key

    return data


def get_alt_az(times_mjd: list, ra: float, dec: float) -> tuple:
    """
    Get alt and az for a target at various times in decimal degrees
    :param times_mjd: list of times
    :param ra: ra
    :param dec: dec
    :return: alt array, and az array
    """
    loc = SkyCoord(ra=ra, dec=dec, frame="icrs")
    time = Time(times_mjd, format="mjd")
    altaz = loc.transform_to(AltAz(obstime=time, location=PALOMAR_LOC))
    degs = SkyCoord(altaz.az, altaz.alt, frame="icrs")
    alt_array = degs.dec.degree
    az_array = degs.ra.degree
    return alt_array, az_array


def up_tonight(time_mjd: astropy.time.Time, ra: str, dec: str) -> tuple[bool, str]:
    """
    what is up (above altitude 20 deg) in a given night?
    date in MJD (median Julian Date), e.g. 59480 (Sept 23)
    ra (right ascension) in hours, minutes, seconds, e.g. '+19h50m41s'
    dec (declination) in hours, minutes, seconds, e.g. '+08d50m58s'
    :param time_mjd: time in mjd
    :param ra: ra of target
    :param dec: dec of target
    :return:
    """
    loc = SkyCoord(ra=ra, dec=dec, frame="icrs")
    time = Time(time_mjd, format="mjd")
    sun_rise = palomar_observer.sun_rise_time(time, which="previous")
    sun_set = palomar_observer.sun_set_time(time, which="next")
    night = sun_set.jd - sun_rise.jd
    if night >= 1:
        # if next day, subtract a day
        time_array = np.linspace(sun_set.jd, sun_set.jd + (night - 1), 100)
    else:
        time_array = np.linspace(sun_set.jd, sun_set.jd + night, 100)

    altaz = loc.transform_to(
        AltAz(obstime=Time(time_array, format="jd"), location=PALOMAR_LOC)
    )
    df = pd.DataFrame(data={"time": time_array, "alt": altaz.alt})
    df = df[df["alt"] >= MINIMUM_ELEVATION]

    try:
        time_up = df["time"].iloc[-1] - df["time"].iloc[0]
    except KeyError:
        time_up = 0

    if time_up > 0:
        is_available = (
            f"Object is up between UTC "
            f'{Time(df["time"].iloc[0], format="jd").isot} '
            f'and {Time(df["time"].iloc[-1], format="jd").isot}'
        )
        avail_bool = True
    else:
        is_available = "Object is not up"
        avail_bool = False

    return avail_bool, is_available